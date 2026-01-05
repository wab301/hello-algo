#!/usr/bin/env python3
"""
代码审查工具测试脚本
"""

import json
import subprocess
import sys


def test_code_reviewer():
    """测试代码审查工具"""
    print("=" * 60)
    print("测试代码审查工具")
    print("=" * 60)
    
    # 测试示例 diff 文件
    print("\n测试 1: 使用示例 diff 文件")
    print("-" * 60)
    
    result = subprocess.run(
        ["python", "tools/code_reviewer.py", "tools/example_diff.txt"],
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        print(f"错误: {result.stderr}")
        return False
    
    try:
        comments = json.loads(result.stdout)
        print(f"✓ 成功检测到 {len(comments)} 个问题")
        
        # 验证输出格式
        for comment in comments:
            assert "file" in comment, "缺少 'file' 字段"
            assert "line" in comment, "缺少 'line' 字段"
            assert "severity" in comment, "缺少 'severity' 字段"
            assert "message" in comment, "缺少 'message' 字段"
            assert "suggestion" in comment, "缺少 'suggestion' 字段"
            assert comment["severity"] in ["error", "warning", "info"], "severity 值无效"
        
        print("✓ 输出格式验证通过")
        
        # 打印部分结果
        print("\n示例问题 (前 3 个):")
        for i, comment in enumerate(comments[:3], 1):
            print(f"\n{i}. {comment['file']}:{comment['line']}")
            print(f"   严重程度: {comment['severity']}")
            print(f"   问题: {comment['message']}")
            print(f"   建议: {comment['suggestion']}")
        
    except json.JSONDecodeError as e:
        print(f"错误: 无法解析 JSON 输出 - {e}")
        print(f"输出内容: {result.stdout}")
        return False
    
    # 测试空 diff (应该返回 "未发现明显问题")
    print("\n\n测试 2: 空 diff")
    print("-" * 60)
    
    empty_diff = "diff --git a/test.txt b/test.txt\n"
    result = subprocess.run(
        ["python", "tools/code_reviewer.py", "-"],
        input=empty_diff,
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        print(f"错误: {result.stderr}")
        return False
    
    try:
        output = json.loads(result.stdout)
        if isinstance(output, dict) and output.get("status") == "ok":
            print("✓ 正确处理空 diff")
        elif isinstance(output, list) and len(output) == 0:
            print("✓ 正确处理空 diff (返回空列表)")
    except json.JSONDecodeError as e:
        print(f"错误: 无法解析 JSON 输出 - {e}")
        return False
    
    print("\n" + "=" * 60)
    print("所有测试通过！")
    print("=" * 60)
    return True


if __name__ == "__main__":
    success = test_code_reviewer()
    sys.exit(0 if success else 1)
