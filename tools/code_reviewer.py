#!/usr/bin/env python3
"""
代码审查工具 (Code Review Tool)

该工具用于分析代码变更（diff），并提供结构化的审查反馈。
重点关注：
1. 逻辑正确性
2. 并发/性能/内存
3. 安全风险
4. 可维护性
5. 是否符合常见工程最佳实践
"""

import json
import re
import sys
from typing import List, Dict, Any
from dataclasses import dataclass, asdict


@dataclass
class ReviewComment:
    """代码审查意见"""
    file: str
    line: int
    severity: str  # "error", "warning", "info"
    message: str
    suggestion: str


class CodeReviewer:
    """代码审查器"""
    
    def __init__(self):
        self.comments: List[ReviewComment] = []
        
    def review_diff(self, diff_content: str) -> List[Dict[str, Any]]:
        """
        审查代码差异
        
        Args:
            diff_content: git diff 格式的内容
            
        Returns:
            审查意见列表
        """
        self.comments = []
        
        # 解析 diff 内容
        files = self._parse_diff(diff_content)
        
        # 对每个文件进行审查
        for file_info in files:
            self._review_file(file_info)
        
        # 转换为 JSON 格式
        return [asdict(comment) for comment in self.comments]
    
    def _parse_diff(self, diff_content: str) -> List[Dict[str, Any]]:
        """解析 diff 内容"""
        files = []
        current_file = None
        current_hunk = None
        
        lines = diff_content.split('\n')
        for line in lines:
            # 文件头
            if line.startswith('diff --git'):
                if current_file:
                    files.append(current_file)
                current_file = {
                    'path': '',
                    'hunks': [],
                    'changes': []
                }
                current_hunk = None
            
            # 新文件路径
            elif line.startswith('+++'):
                match = re.search(r'\+\+\+ b/(.+)', line)
                if match and current_file:
                    current_file['path'] = match.group(1)
            
            # 代码块头
            elif line.startswith('@@'):
                match = re.search(r'@@ -\d+,?\d* \+(\d+),?\d* @@', line)
                if match and current_file:
                    current_hunk = {
                        'start_line': int(match.group(1)),
                        'changes': []
                    }
                    current_file['hunks'].append(current_hunk)
            
            # 代码变更
            elif current_hunk and (line.startswith('+') or line.startswith('-') or line.startswith(' ')):
                change_type = 'add' if line.startswith('+') else ('remove' if line.startswith('-') else 'context')
                current_hunk['changes'].append({
                    'type': change_type,
                    'content': line[1:] if len(line) > 0 else '',
                    'line': line
                })
        
        if current_file:
            files.append(current_file)
        
        return files
    
    def _review_file(self, file_info: Dict[str, Any]):
        """审查单个文件的变更"""
        file_path = file_info['path']
        
        # 跳过非代码文件
        if not self._is_code_file(file_path):
            return
        
        # 对每个代码块进行审查
        for hunk in file_info['hunks']:
            line_num = hunk['start_line']
            
            for i, change in enumerate(hunk['changes']):
                if change['type'] == 'add':
                    content = change['content']
                    
                    # 检查各种问题
                    self._check_concurrency_issues(file_path, line_num, content)
                    self._check_security_issues(file_path, line_num, content)
                    self._check_performance_issues(file_path, line_num, content)
                    self._check_code_quality(file_path, line_num, content)
                    
                    line_num += 1
                elif change['type'] == 'context':
                    line_num += 1
    
    def _is_code_file(self, file_path: str) -> bool:
        """判断是否为代码文件"""
        code_extensions = ['.go', '.py', '.java', '.js', '.ts', '.cpp', '.c', '.cs', '.rs', '.swift']
        return any(file_path.endswith(ext) for ext in code_extensions)
    
    def _check_concurrency_issues(self, file_path: str, line_num: int, content: str):
        """检查并发问题"""
        # 检查 Go 语言的 mutex 使用
        if file_path.endswith('.go'):
            # 未加锁的共享状态访问
            if 'map[' in content and 'sync.Mutex' not in content and 'Lock()' not in content:
                if any(keyword in content for keyword in ['go func', 'goroutine']):
                    self.comments.append(ReviewComment(
                        file=file_path,
                        line=line_num,
                        severity="warning",
                        message="可能存在并发访问 map 的竞态条件",
                        suggestion="考虑使用 sync.Map 或添加互斥锁保护"
                    ))
            
            # 检查未保护的共享变量
            if re.search(r'\bgo\s+func', content):
                self.comments.append(ReviewComment(
                    file=file_path,
                    line=line_num,
                    severity="info",
                    message="启动了 goroutine，请确保正确处理并发访问",
                    suggestion="检查是否需要使用 sync.Mutex 或 channel 进行同步"
                ))
        
        # 检查 Java 的并发问题
        elif file_path.endswith('.java'):
            if 'synchronized' not in content and any(word in content for word in ['HashMap', 'ArrayList', 'HashSet']):
                if 'Thread' in content or 'Executor' in content:
                    self.comments.append(ReviewComment(
                        file=file_path,
                        line=line_num,
                        severity="warning",
                        message="多线程环境下使用非线程安全的集合",
                        suggestion="考虑使用 ConcurrentHashMap 或添加同步控制"
                    ))
    
    def _check_security_issues(self, file_path: str, line_num: int, content: str):
        """检查安全问题"""
        # SQL 注入
        if any(keyword in content.lower() for keyword in ['select', 'insert', 'update', 'delete']):
            if '+' in content or 'fmt.Sprintf' in content or 'String.format' in content:
                self.comments.append(ReviewComment(
                    file=file_path,
                    line=line_num,
                    severity="error",
                    message="可能存在 SQL 注入风险",
                    suggestion="使用参数化查询或 ORM 框架，避免字符串拼接"
                ))
        
        # 密码/密钥硬编码
        if any(keyword in content.lower() for keyword in ['password', 'secret', 'token', 'api_key', 'apikey']):
            if '=' in content and ('"' in content or "'" in content):
                if not any(func in content for func in ['os.Getenv', 'System.getenv', 'process.env']):
                    self.comments.append(ReviewComment(
                        file=file_path,
                        line=line_num,
                        severity="error",
                        message="可能存在敏感信息硬编码",
                        suggestion="使用环境变量或配置文件管理敏感信息"
                    ))
        
        # 命令注入
        if any(func in content for func in ['exec', 'system', 'eval', 'Runtime.getRuntime']):
            self.comments.append(ReviewComment(
                file=file_path,
                line=line_num,
                severity="warning",
                message="使用了可能不安全的命令执行函数",
                suggestion="验证输入参数，避免注入攻击"
            ))
        
        # XSS 风险
        if file_path.endswith(('.html', '.js', '.jsx', '.ts', '.tsx')):
            if 'innerHTML' in content or 'dangerouslySetInnerHTML' in content:
                self.comments.append(ReviewComment(
                    file=file_path,
                    line=line_num,
                    severity="warning",
                    message="直接设置 HTML 内容可能导致 XSS 攻击",
                    suggestion="使用安全的 DOM 操作方法或进行内容转义"
                ))
    
    def _check_performance_issues(self, file_path: str, line_num: int, content: str):
        """检查性能问题"""
        # 循环中的字符串拼接
        if any(keyword in content for keyword in ['for', 'while']):
            if '+=' in content and ('"' in content or "'" in content):
                self.comments.append(ReviewComment(
                    file=file_path,
                    line=line_num,
                    severity="info",
                    message="循环中使用字符串拼接可能影响性能",
                    suggestion="考虑使用 StringBuilder 或类似的高效方式"
                ))
        
        # 嵌套循环
        if content.count('for') > 1 or content.count('while') > 1:
            self.comments.append(ReviewComment(
                file=file_path,
                line=line_num,
                severity="info",
                message="存在嵌套循环，注意时间复杂度",
                suggestion="评估是否可以优化算法复杂度"
            ))
        
        # 未关闭的资源
        if any(keyword in content for keyword in ['open(', 'File(', 'Connection', 'Stream']):
            if 'close()' not in content and 'with' not in content and 'defer' not in content:
                self.comments.append(ReviewComment(
                    file=file_path,
                    line=line_num,
                    severity="warning",
                    message="打开资源后可能未正确关闭",
                    suggestion="使用 with/defer/try-finally 确保资源释放"
                ))
    
    def _check_code_quality(self, file_path: str, line_num: int, content: str):
        """检查代码质量"""
        # 魔术数字
        if re.search(r'\b\d{2,}\b', content) and 'const' not in content and 'final' not in content:
            if not any(keyword in content for keyword in ['return', 'range', 'len(', 'size()']):
                self.comments.append(ReviewComment(
                    file=file_path,
                    line=line_num,
                    severity="info",
                    message="存在魔术数字",
                    suggestion="将数字提取为有意义的常量"
                ))
        
        # 过长的行
        if len(content) > 120:
            self.comments.append(ReviewComment(
                file=file_path,
                line=line_num,
                severity="info",
                message="代码行过长，影响可读性",
                suggestion="考虑拆分为多行"
            ))
        
        # TODO/FIXME 注释
        if 'TODO' in content or 'FIXME' in content:
            self.comments.append(ReviewComment(
                file=file_path,
                line=line_num,
                severity="info",
                message="存在待办事项标记",
                suggestion="确保在合并前处理或创建跟踪任务"
            ))
        
        # 空异常处理
        if ('except:' in content or 'catch' in content) and ('pass' in content or '{}' in content):
            self.comments.append(ReviewComment(
                file=file_path,
                line=line_num,
                severity="warning",
                message="空的异常处理块",
                suggestion="至少记录日志或重新抛出异常"
            ))


def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("用法: python code_reviewer.py <diff_file>")
        print("或通过管道输入: git diff | python code_reviewer.py")
        sys.exit(1)
    
    reviewer = CodeReviewer()
    
    # 读取 diff 内容
    if sys.argv[1] == '-':
        diff_content = sys.stdin.read()
    else:
        try:
            with open(sys.argv[1], 'r', encoding='utf-8') as f:
                diff_content = f.read()
        except FileNotFoundError:
            print(f"错误: 文件 {sys.argv[1]} 不存在")
            sys.exit(1)
    
    # 执行审查
    comments = reviewer.review_diff(diff_content)
    
    # 输出结果
    if not comments:
        print(json.dumps({"status": "ok", "message": "未发现明显问题"}, 
                        ensure_ascii=False, indent=2))
    else:
        print(json.dumps(comments, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
