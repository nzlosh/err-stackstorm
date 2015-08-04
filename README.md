#err-stackstorm

This plugin can run action-alias in stackstorm

**important: not support st2 auth now,If you want,It is easy to add by yourself.**

##Install
```
!repos install https://github.com/fmnisme/err-stackstorm.git
```

##Edit config.py
```
ST2={
    'st2_base_url': 'http://localhost',
    'st2_auth_url': 'https://localhost:9100',
    'st2_api_url': 'http://localhost:9101/v1',
    'st2_api_version': 'v1',
    'timer_update': 60, #second. auto update patterns and help from st2.
}
```
##Command
1. write alias in stackstorm
2. type `!helpst2` in errbot

##How to send message from stackstorm to errbot?
If you want to send msg from stackstorm to errbot,you should write a simple httpserver in your backend, and post message to your backend just like `hubot.post_message` does in stackstorm.