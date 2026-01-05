# 使用指南

## 快速开始

### 1. 安装依赖

代码审查工具使用 Python 3 标准库，无需额外安装依赖。

### 2. 基本使用

#### 审查当前未提交的更改

```bash
git diff | python tools/code_reviewer.py -
```

#### 审查已暂存的更改

```bash
git diff --staged | python tools/code_reviewer.py -
```

#### 审查特定提交

```bash
git show <commit-hash> | python tools/code_reviewer.py -
```

#### 审查两个分支之间的差异

```bash
git diff main..feature-branch | python tools/code_reviewer.py -
```

#### 从文件读取 diff

```bash
git diff > changes.diff
python tools/code_reviewer.py changes.diff
```

### 3. 测试工具

运行测试脚本验证工具功能：

```bash
python tools/test_code_reviewer.py
```

### 4. 使用示例

查看示例 diff 文件的审查结果：

```bash
python tools/code_reviewer.py tools/example_diff.txt
```

## 输出示例

工具输出 JSON 格式，每个问题包含以下字段：

```json
{
  "file": "example/login/auth.go",
  "line": 21,
  "severity": "error",
  "message": "可能存在敏感信息硬编码",
  "suggestion": "使用环境变量或配置文件管理敏感信息"
}
```

### 严重程度说明

- **error**: 严重问题，可能导致安全漏洞或严重 bug，**必须修复**
- **warning**: 警告，可能导致潜在问题，**强烈建议修复**
- **info**: 提示信息，代码改进建议，可选修复

## 检测规则详解

### 并发安全 (Concurrency)

#### Go 语言

- **未加锁的 map 访问**: 在 goroutine 中访问 map 而未使用 sync.Mutex
  ```go
  // ❌ 问题代码
  go func() {
      userCache["key"] = value  // 并发写入
  }()
  
  // ✓ 修复建议
  mu.Lock()
  userCache["key"] = value
  mu.Unlock()
  ```

- **goroutine 启动提醒**: 提醒检查并发访问控制
  ```go
  // 启动 goroutine 时，确保正确处理共享状态
  go processData(sharedData)
  ```

#### Java 语言

- **非线程安全集合**: 多线程环境下使用 HashMap、ArrayList 等
  ```java
  // ❌ 问题代码
  private HashMap<String, User> cache = new HashMap<>();
  
  // ✓ 修复建议
  private ConcurrentHashMap<String, User> cache = new ConcurrentHashMap<>();
  ```

### 安全风险 (Security)

#### SQL 注入

检测字符串拼接的 SQL 语句：

```go
// ❌ 问题代码
query := "SELECT * FROM users WHERE id = '" + userId + "'"

// ✓ 修复建议 - 使用参数化查询
query := "SELECT * FROM users WHERE id = ?"
db.Query(query, userId)
```

```java
// ❌ 问题代码
String sql = "SELECT * FROM users WHERE username = '" + username + "'";

// ✓ 修复建议 - 使用 PreparedStatement
String sql = "SELECT * FROM users WHERE username = ?";
PreparedStatement stmt = conn.prepareStatement(sql);
stmt.setString(1, username);
```

#### 敏感信息硬编码

检测硬编码的密码、密钥、token：

```go
// ❌ 问题代码
const apiKey = "sk-1234567890abcdef"
password := "admin123"

// ✓ 修复建议 - 使用环境变量
apiKey := os.Getenv("API_KEY")
password := os.Getenv("ADMIN_PASSWORD")
```

```python
# ❌ 问题代码
API_KEY = "sk-1234567890abcdef"

# ✓ 修复建议 - 使用环境变量
import os
API_KEY = os.getenv("API_KEY")
```

#### 命令注入

检测不安全的命令执行：

```python
# ❌ 问题代码
import os
os.system(user_input)

# ✓ 修复建议 - 验证输入
import subprocess
import shlex
subprocess.run(shlex.split(validated_command))
```

```javascript
// ❌ 问题代码
const { exec } = require('child_process');
exec(userInput);

// ✓ 修复建议 - 使用 execFile 并验证参数
const { execFile } = require('child_process');
execFile(command, validatedArgs);
```

#### XSS 跨站脚本攻击

检测直接 HTML 注入：

```javascript
// ❌ 问题代码
element.innerHTML = userInput;

// ✓ 修复建议 - 使用安全方法
element.textContent = userInput;
// 或使用 DOMPurify 等库
element.innerHTML = DOMPurify.sanitize(userInput);
```

### 性能问题 (Performance)

#### 循环中的字符串拼接

```go
// ❌ 问题代码
result := ""
for _, item := range items {
    result += item  // 效率低
}

// ✓ 修复建议
var builder strings.Builder
for _, item := range items {
    builder.WriteString(item)
}
result := builder.String()
```

```java
// ❌ 问题代码
String result = "";
for (String item : items) {
    result += item;  // 效率低
}

// ✓ 修复建议
StringBuilder builder = new StringBuilder();
for (String item : items) {
    builder.append(item);
}
String result = builder.toString();
```

#### 嵌套循环

```python
# 注意时间复杂度 O(n²)
for i in range(n):
    for j in range(n):
        process(i, j)

# 考虑优化算法，例如使用哈希表
```

#### 资源未关闭

```python
# ❌ 问题代码
file = open("data.txt")
data = file.read()

# ✓ 修复建议
with open("data.txt") as file:
    data = file.read()
```

```go
// ❌ 问题代码
file, _ := os.Open("data.txt")
data, _ := io.ReadAll(file)

// ✓ 修复建议
file, err := os.Open("data.txt")
if err != nil {
    return err
}
defer file.Close()
data, err := io.ReadAll(file)
```

### 代码质量 (Code Quality)

#### 魔术数字

```go
// ❌ 问题代码
if count > 100 {
    // ...
}

// ✓ 修复建议
const MaxItems = 100
if count > MaxItems {
    // ...
}
```

#### 空异常处理

```python
# ❌ 问题代码
try:
    risky_operation()
except:
    pass  # 忽略所有错误

# ✓ 修复建议
try:
    risky_operation()
except SpecificError as e:
    logger.error(f"Operation failed: {e}")
    raise
```

```java
// ❌ 问题代码
try {
    riskyOperation();
} catch (Exception e) {
    // 空处理
}

// ✓ 修复建议
try {
    riskyOperation();
} catch (Exception e) {
    logger.error("Operation failed", e);
    throw e;
}
```

#### TODO/FIXME 标记

```python
# TODO: 实现用户删除功能
# FIXME: 修复登录超时问题
```

确保在合并前处理这些标记，或创建跟踪任务。

## 集成到开发流程

### Pre-commit Hook

创建 `.git/hooks/pre-commit` 文件：

```bash
#!/bin/bash
git diff --staged | python tools/code_reviewer.py - > /tmp/review.json
if [ -s /tmp/review.json ]; then
    echo "发现代码问题，请查看 /tmp/review.json"
    cat /tmp/review.json
    exit 1
fi
```

### IDE 集成

#### VS Code

在 `.vscode/tasks.json` 中添加：

```json
{
  "version": "2.0.0",
  "tasks": [
    {
      "label": "Code Review",
      "type": "shell",
      "command": "git diff | python tools/code_reviewer.py -",
      "problemMatcher": []
    }
  ]
}
```

### CI/CD 集成

参见仓库中的 `.github/workflows/code_review.yml`

## 常见问题

### Q: 工具报告了误报怎么办？

A: 工具基于静态分析和模式匹配，可能产生误报。请根据实际情况判断，忽略不适用的建议。

### Q: 如何添加自定义检查规则？

A: 编辑 `tools/code_reviewer.py`，在相应的检查方法中添加规则。

### Q: 工具支持哪些编程语言？

A: 目前支持 Go、Python、Java、JavaScript/TypeScript、C/C++、C#、Rust、Swift 等。

### Q: 如何调整检查规则的严格程度？

A: 修改 `code_reviewer.py` 中各检查方法的 `severity` 参数。

## 最佳实践

1. **定期运行**: 在提交前运行工具检查
2. **结合人工审查**: 工具不能替代人工代码审查
3. **持续改进**: 根据项目特点调整检查规则
4. **团队共识**: 与团队讨论审查标准，形成共识
5. **记录决策**: 对于忽略的警告，添加注释说明原因

## 扩展阅读

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Go 并发编程最佳实践](https://go.dev/doc/effective_go#concurrency)
- [Java 并发编程](https://docs.oracle.com/javase/tutorial/essential/concurrency/)
- [Secure Coding Guidelines](https://wiki.sei.cmu.edu/confluence/display/seccode)
