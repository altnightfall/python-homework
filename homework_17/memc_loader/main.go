package main

import (
	"bufio"
	"compress/gzip"
	"flag"
	"fmt"
	"log"
	"os"
	"path/filepath"
	"strconv"
	"strings"
	"sync"

	"github.com/bradfitz/gomemcache/memcache"
	"google.golang.org/protobuf/proto"

	"memc_loader/appsinstalledpb"
)

const normalErrRate = 0.01

type AppsInstalled struct {
	DevType string
	DevID   string
	Lat     float64
	Lon     float64
	Apps    []int32
}

func dotRename(path string) {
	dir, file := filepath.Split(path)
	os.Rename(path, filepath.Join(dir, "."+file))
}

func insertAppsInstalled(memcAddr string, ai *AppsInstalled, dry bool) error {
	ua := &appsinstalledpb.UserApps{
		Lat:  proto.Float64(ai.Lat),
		Lon:  proto.Float64(ai.Lon),
		Apps: make([]uint32, len(ai.Apps)),
	}
	for i, a := range ai.Apps {
		ua.Apps[i] = uint32(a)
	}
	packed, err := proto.Marshal(ua)
	if err != nil {
		return fmt.Errorf("failed to marshal protobuf: %v", err)
	}

	key := fmt.Sprintf("%s:%s", ai.DevType, ai.DevID)

	if dry {
		log.Printf("%s - %s -> %v", memcAddr, key, ua)
		return nil
	}

	mc := memcache.New(memcAddr)
	err = mc.Set(&memcache.Item{Key: key, Value: packed})
	if err != nil {
		return fmt.Errorf("memcache set failed: %v", err)
	}
	return nil
}

func parseAppsInstalled(line string) *AppsInstalled {
	parts := strings.Split(line, "\t")
	if len(parts) < 5 {
		return nil
	}
	devType, devID, latS, lonS, rawApps := parts[0], parts[1], parts[2], parts[3], parts[4]
	if devType == "" || devID == "" {
		return nil
	}
	var ai AppsInstalled
	ai.DevType = devType
	ai.DevID = devID

	var err error
	ai.Lat, err = parseFloat(latS)
	if err != nil {
		log.Printf("Invalid lat: %s", line)
		return nil
	}
	ai.Lon, err = parseFloat(lonS)
	if err != nil {
		log.Printf("Invalid lon: %s", line)
		return nil
	}

	for _, a := range strings.Split(rawApps, ",") {
		a = strings.TrimSpace(a)
		if a == "" {
			continue
		}
		val, err := parseInt(a)
		if err != nil {
			log.Printf("Non-digit app: %s", a)
			continue
		}
		ai.Apps = append(ai.Apps, val)
	}

	return &ai
}

func parseFloat(s string) (float64, error) {
	return strconv.ParseFloat(s, 64)
}

func parseInt(s string) (int32, error) {
	v, err := strconv.Atoi(s)
	return int32(v), err
}

func processFile(fn string, deviceMemc map[string]string, dry bool, maxWorkers int) {
	log.Printf("Processing %s", fn)
	f, err := os.Open(fn)
	if err != nil {
		log.Printf("Cannot open file %s: %v", fn, err)
		return
	}
	defer f.Close()

	gz, err := gzip.NewReader(f)
	if err != nil {
		log.Printf("Cannot open gzip %s: %v", fn, err)
		return
	}
	defer gz.Close()

	scanner := bufio.NewScanner(gz)
	var lines []string
	for scanner.Scan() {
		line := strings.TrimSpace(scanner.Text())
		if line != "" {
			lines = append(lines, line)
		}
	}

	var processed, errors int
	wg := sync.WaitGroup{}
	sem := make(chan struct{}, maxWorkers)
	mu := sync.Mutex{}

	for _, line := range lines {
		ai := parseAppsInstalled(line)
		if ai == nil {
			errors++
			continue
		}
		memcAddr, ok := deviceMemc[ai.DevType]
		if !ok {
			log.Printf("Unknown device type: %s", ai.DevType)
			errors++
			continue
		}

		wg.Add(1)
		sem <- struct{}{}
		go func(ai *AppsInstalled, memcAddr string) {
			defer wg.Done()
			err := insertAppsInstalled(memcAddr, ai, dry)
			mu.Lock()
			if err != nil {
				errors++
				log.Printf("Insert error: %v", err)
			} else {
				processed++
			}
			mu.Unlock()
			<-sem
		}(ai, memcAddr)
	}
	wg.Wait()

	if processed == 0 {
		dotRename(fn)
		return
	}

	errRate := float64(errors) / float64(processed)
	if errRate < normalErrRate {
		log.Printf("Acceptable error rate (%f). Successful load", errRate)
	} else {
		log.Printf("High error rate (%f > %f). Failed load", errRate, normalErrRate)
	}

	dotRename(fn)
}

func main() {
	pattern := flag.String("pattern", "data/*.tsv.gz", "Input file pattern")
	idfa := flag.String("idfa", "127.0.0.1:33013", "IDFA memcache")
	gaid := flag.String("gaid", "127.0.0.1:33014", "GAID memcache")
	adid := flag.String("adid", "127.0.0.1:33015", "ADID memcache")
	dvid := flag.String("dvid", "127.0.0.1:33016", "DVID memcache")
	dry := flag.Bool("dry", false, "Dry run")
	flag.Parse()

	deviceMemc := map[string]string{
		"idfa": *idfa,
		"gaid": *gaid,
		"adid": *adid,
		"dvid": *dvid,
	}

	files, err := filepath.Glob(*pattern)
	if err != nil {
		log.Fatalf("Glob pattern error: %v", err)
	}

	for _, fn := range files {
		processFile(fn, deviceMemc, *dry, 8)
	}
}
