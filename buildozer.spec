[app]
title = База Артикулов
package.name = bazaarticuli
package.domain = org.baza
source.dir = .
source.include_exts = py,png,jpg,kv,atlas
version = 1.0.0
requirements = python3,kivy==2.3.0,kivymd==1.1.1,requests,urllib3,chardet,idna
orientation = portrait
fullscreen = 0
android.permissions = INTERNET
android.api = 33
android.minapi = 21
android.ndk_api = 21
android.archs = arm64-v8a, armeabi-v7a
p4a.branch = master
android.python_version = 3.10

[buildozer]
log_level = 2
warn_on_root = 1
