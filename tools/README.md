# 代码审查工具 (Code Review Tool)

## 简介

这是一个自动化代码审查工具，用于分析代码变更（diff）并提供结构化的审查反馈。

## 功能特性

该工具重点关注以下方面：

1. **逻辑正确性** - 检查代码逻辑错误
2. **并发/性能/内存** - 识别并发问题、性能瓶颈和内存泄漏
3. **安全风险** - 检测 SQL 注入、XSS、命令注入、敏感信息泄露等安全问题
4. **可维护性** - 评估代码可读性和维护性
5. **工程最佳实践** - 确保符合常见的工程标准

## 安装

无需额外安装，工具使用 Python 3 标准库。

## 使用方法

### 基本用法

```bash
# 方式 1: 从文件读取 diff
python tools/code_reviewer.py diff.txt

# 方式 2: 从管道输入
git diff | python tools/code_reviewer.py -

# 方式 3: 审查特定提交
git show <commit-hash> | python tools/code_reviewer.py -

# 方式 4: 审查当前未提交的更改
git diff HEAD | python tools/code_reviewer.py -
```

### 示例

```bash
# 审查最近一次提交
git show HEAD | python tools/code_reviewer.py -

# 审查两个分支之间的差异
git diff main..feature-branch | python tools/code_reviewer.py -

# 审查暂存区的更改
git diff --staged | python tools/code_reviewer.py -
```

## 输出格式

工具输出 JSON 格式的审查意见，每条意见包含：

```json
{
  "file": "login/auth.go",
  "line": 135,
  "severity": "warning",
  "message": "这里的 mutex 未覆盖所有共享状态，可能存在竞态条件",
  "suggestion": "考虑将 tokenCache 的读写统一放入临界区"
}
```

### 字段说明

- `file`: 文件路径
- `line`: 行号
- `severity`: 严重程度
  - `error`: 错误，必须修复
  - `warning`: 警告，强烈建议修复
  - `info`: 提示，可选修复
- `message`: 问题描述
- `suggestion`: 修复建议

## 检查规则

### 并发问题

- **Go**: 检查未保护的 map 访问、goroutine 使用
- **Java**: 检查多线程环境下非线程安全集合的使用

### 安全问题

- **SQL 注入**: 检测字符串拼接的 SQL 语句
- **敏感信息泄露**: 检测硬编码的密码、密钥
- **命令注入**: 检测不安全的命令执行
- **XSS 攻击**: 检测直接 HTML 注入

### 性能问题

- 循环中的字符串拼接
- 嵌套循环
- 未关闭的资源

### 代码质量

- 魔术数字
- 过长的代码行
- 空的异常处理
- TODO/FIXME 标记

## 支持的语言

- Go (.go)
- Python (.py)
- Java (.java)
- JavaScript/TypeScript (.js, .ts, .jsx, .tsx)
- C/C++ (.c, .cpp)
- C# (.cs)
- Rust (.rs)
- Swift (.swift)

## 集成到 CI/CD

### GitHub Actions

```yaml
name: Code Review

on:
  pull_request:
    branches: [ main ]

jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      
      - name: Run Code Review
        run: |
          git diff origin/main...HEAD | python tools/code_reviewer.py - > review_results.json
      
      - name: Upload Review Results
        uses: actions/upload-artifact@v3
        with:
          name: review-results
          path: review_results.json
```

### GitLab CI

```yaml
code_review:
  stage: test
  script:
    - git diff origin/main...HEAD | python tools/code_reviewer.py - > review_results.json
  artifacts:
    paths:
      - review_results.json
```

## 限制

- 工具基于静态分析和模式匹配，可能产生误报
- 不能替代人工代码审查
- 只分析 diff 中的变更部分，不检查整个文件
- 对于复杂的上下文依赖问题可能无法检测

## 贡献

欢迎提交 Issue 和 Pull Request 来改进工具！

## 许可证

与主项目相同，遵循 CC BY-NC-SA-4.0 许可证。
