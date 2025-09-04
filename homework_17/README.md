В этом домашнем задании предлагается переписать конкурентный memcache loader, реализованный на Python в одном из прошлых заданий, на Golang, соблюдая при этом идиоматику языка и используя его возможности, рассмотренные на занятии

build on Windows (PowerShell):
```
$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine")
cd memc_loader
go mod tidy
go build -o memc_load.exe main.go
```

run dry:
```
.\memc_load.exe -pattern ".\data\*.tsv.gz" -dry true
```
run:
```
.\memc_load.exe -pattern ".\data\*.tsv.gz" -dry true
```
help:
```
.\memc_load.exe -h
```