# Описание
Жил-был чудный веб-интерфейса и все у него было хорошо: в него ходили
пользователи, что-то там кликали, переходили по ссылкам, получали результат. Но
со временем некоторые его странички стали тупить и долго грузиться. Менеджеры
часто жалуются, мол "вот тут список долго грузился" или "интерфейсик тупит,
поиск не работает". Но так трудно отделить те случаи, где проблемы на их стороне,
а где действительно виноват веб-сервис. В логи reverse proxy перед интерфейсом
(nginx) добавили время запроса ($request_time в nginx
http://nginx.org/en/docs/http/ngx_http_log_module.html#log_format). Теперь можно
распарсить логи и провести первичный анализ, выявив подозрительные URL'ы.

## Запуск
It is recommended to always work in a virtual environment to avoid cluttering the system. A Makefile has been created with basic commands for convenience.
To install dependencies for log_parser, run the following command:
```bash
$> make install
```

This command will create a virtual environment in the `.venv` folder and install the required dependencies into it for the application to work.

For running scripts, use the following option:
```bash
$> python src/log_analyzer.py
```

You can change settings in the `src/config.py` file.
```json
{
 "REPORT_SIZE": 1000,
 "REPORT_DIR": "./reports",
 "LOG_DIR": "./log"
}

```
