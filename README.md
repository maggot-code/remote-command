背景：
实现一个可以远程执行命令的服务，整体项目使用python开发，服务端使用django作为API Server对外提供给服务；
利用python调用ansible-runner api实现具体业务逻辑；通过uv管理python环境，并为该项目创建独立的虚拟环境（venv）；

重点：
优先完成Linux平台的整体业务流程，有关于Windows的部分则全部pass（但是要保留和创建相关文件内容，函数可以暂时pass）

版本：
Python==3.9.6
Ansible==跟随Python版本可用的最新版本

需求：
1. 服务整体使用方式为对外提供API Server调用
2. 同时支持Linux和Windows双平台远程执行命令
3. 要求实现Linux和Windows双平台的免密执行命令和脚本

接口：
1. /command：通过传入IP、username、password、port、command、os_type参数实现远程命令执行
2. /nopwd/command：通过传入IP、username、port、command、os_type参数实现免密远程命令执行
3. /script：通过传入IP、username、port、file_path、remote_host、os_type参数实现免密执行本地脚本，使其运行在远端服务器上

规划：
1. Linux和Windows的具体业务逻辑分开实现，但是能够复用部分要求必须服用
2. ansible相关的拼接配置要求使用模板实现，模板中保留变量空缺，通过从API Server接收参数后替换模板变量
3. API层仅做参数合法校验，不做业务逻辑校验
4. Service层实现业务编排并完成参数的业务逻辑校验
5. Biz层实现具体与ansible-runner api相关的调用业务逻辑
6. Config层配置模板文件、os_type类型、port默认端口
7. 暂时不引入存储相关能力
8. 要求引入日志（log）能力，区分日志类型（Server Log、Ansible Log）
9. 要求引入错误（error）能力，区分错误类型（Server Error、Ansible Error）

测试：
Linux：192.168.27.10 root/123