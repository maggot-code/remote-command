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

调整：
1. 合并接口，API层依然仅完成参数合法性校验，同时通过os_type选择对应service层对应的平台调用
2. service层校验password是否可用，用于调用对应的biz层业务实例
3. service层完全处理具体的业务参数，包括但不限于参数选择、参数默认值填充等

后续计划：
1. **deploy部分开发，提供不同的部署方式（可执行文件部署、远端脚本部署、镜像部署**
2. 补全windows相关功能
3. 抽离业务逻辑，找到可复用部分重构
4. 为ansible增加对应模块的业务模板

# 重构设计
## 接口：/remote_call
参数：
1. os_type string required [linux | windows]
2. ip string required
3. username string required
4. password string
5. port number
6. command string
7. file_path string
## 伪代码
```python
def remote_call(request):
    # 参数合法性校验
    value_err = parameter_verification(request.data)
    if(value_err):
        return Response(value_err)

    # 基础信息准备
    port = confirm_port(request.data.get("os_type"),request.data.get("password"),request.data.get("port"))
    host_pattern = confirm_host_pattern(request.data.get("os_type"))
    public_temp = confirm_public_template(request.data.get("os_type"))
    os_temp = confirm_os_template(request.data.get("os_type"),port)

    # 打包
    inventory,build_close = build_inventory(host_pattern,public_temp,os_temp,{
        "ip": request.data.get("ip"),
        "username": request.data.get("username"),
        "password": request.data.get("password"),
        "port": port
    })

    # 任务准备
    tasks = []
    if(request.data.get("command")):
        tasks.append(build_command(inventory,host_pattern,request.data.get("command")))
    
    if(request.data.get("file_path")):
        tasks.append(build_command(inventory,host_pattern,request.data.get("file_path")))

    # 执行任务
    result = execute_ansble(tasks)

    # 关闭构建
    build_close()

    if(result.errors):
        return Response(result.errors)

    return Response(result)
```
## 重构目标
1. 提升代码可读性和可维护性
2. 减少重复代码，提取公共逻辑
3. 增强错误处理能力
4. 优化性能，减少不必要的资源消耗
5. 统一返回格式

{
    "ip": "192.168.27.10",
    "username": "root",
    "password":"123",
    "port":22,
    "command":"date",
    "file_path":"/Users/codemaggot/code/remote_command/test/test.sh",
    "os_type": "linux"
}