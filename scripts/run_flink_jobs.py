#!/usr/bin/env python
"""
Flink实时处理作业启动器

支持启动所有Flink作业：
1. user_profile_updater - 用户画像实时更新
2. item_hot_score_calculator - 物品热度实时计算
3. recommendation_metrics - 推荐指标实时统计

启动方式:
    # 启动所有作业
    poetry run python scripts/run_flink_jobs.py --all
    
    # 启动指定作业
    poetry run python scripts/run_flink_jobs.py --job user_profile
    
    # 后台运行
    nohup poetry run python scripts/run_flink_jobs.py --all > logs/flink_jobs.log 2>&1 &
"""
import sys
import os
import argparse
import subprocess
import time
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


FLINK_JOBS = {
    'user_profile': {
        'name': '用户画像实时更新',
        'module': 'flink_jobs.user_profile_updater',
        'description': '从Kafka消费用户行为，5分钟窗口聚合，更新用户画像到MongoDB/Redis'
    },
    'item_hot_score': {
        'name': '物品热度实时计算',
        'module': 'flink_jobs.item_hot_score_calculator',
        'description': '从Kafka消费用户行为，1小时滑动窗口，计算物品热度到Redis ZSET'
    },
    'rec_metrics': {
        'name': '推荐指标实时统计',
        'module': 'flink_jobs.recommendation_metrics',
        'description': '从Kafka消费用户行为，1分钟窗口聚合，推送指标到Prometheus'
    }
}


def print_banner():
    """打印Banner"""
    print("=" * 70)
    print(" " * 15 + "Flink实时处理作业启动器")
    print("=" * 70)
    print()


def list_jobs():
    """列出所有可用作业"""
    print("📊 可用的Flink作业:\n")
    for job_key, job_info in FLINK_JOBS.items():
        print(f"  [{job_key}] {job_info['name']}")
        print(f"      {job_info['description']}")
        print()


def check_dependencies():
    """检查依赖"""
    print("🔍 检查依赖...")
    
    try:
        import pyflink
        print("  ✅ PyFlink已安装")
        return True
    except ImportError:
        print("  ❌ PyFlink未安装")
        print("\n请安装PyFlink:")
        print("  pip install apache-flink")
        return False


def run_job(job_key):
    """运行单个Flink作业"""
    if job_key not in FLINK_JOBS:
        print(f"❌ 未知作业: {job_key}")
        print(f"可用作业: {', '.join(FLINK_JOBS.keys())}")
        return False
    
    job_info = FLINK_JOBS[job_key]
    
    print(f"\n🚀 启动作业: {job_info['name']}")
    print(f"   模块: {job_info['module']}")
    print(f"   描述: {job_info['description']}")
    print()
    
    try:
        # 导入并运行模块
        module = __import__(job_info['module'], fromlist=['main'])
        module.main()
        return True
    except Exception as e:
        print(f"❌ 作业启动失败: {e}")
        return False


def run_all_jobs():
    """并行运行所有Flink作业（使用subprocess）"""
    print("\n🚀 启动所有Flink作业...\n")
    
    processes = []
    
    for job_key, job_info in FLINK_JOBS.items():
        print(f"  启动: {job_info['name']}...")
        
        # 使用subprocess启动独立进程
        cmd = [
            sys.executable,
            '-m', job_info['module']
        ]
        
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=project_root
        )
        
        processes.append({
            'key': job_key,
            'name': job_info['name'],
            'process': proc
        })
        
        time.sleep(2)  # 间隔2秒启动下一个
    
    print(f"\n✅ 已启动 {len(processes)} 个作业")
    print("\n监控作业状态...")
    print("按 Ctrl+C 停止所有作业\n")
    
    try:
        # 监控所有进程
        while True:
            for p in processes:
                if p['process'].poll() is not None:
                    # 进程已退出
                    print(f"⚠️  作业 {p['name']} 已退出")
                    p['process'] = None
            
            time.sleep(5)
    
    except KeyboardInterrupt:
        print("\n\n收到中断信号，停止所有作业...")
        
        for p in processes:
            if p['process'] and p['process'].poll() is None:
                print(f"  停止: {p['name']}...")
                p['process'].terminate()
                p['process'].wait(timeout=10)
        
        print("✅ 所有作业已停止")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='Flink实时处理作业启动器',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
示例:
  # 列出所有作业
  python scripts/run_flink_jobs.py --list
  
  # 启动指定作业
  python scripts/run_flink_jobs.py --job user_profile
  
  # 启动所有作业
  python scripts/run_flink_jobs.py --all
  
  # 检查依赖
  python scripts/run_flink_jobs.py --check
        '''
    )
    
    parser.add_argument('--list', action='store_true', help='列出所有可用作业')
    parser.add_argument('--job', type=str, help='启动指定作业')
    parser.add_argument('--all', action='store_true', help='启动所有作业')
    parser.add_argument('--check', action='store_true', help='检查依赖')
    
    args = parser.parse_args()
    
    print_banner()
    
    # 列出作业
    if args.list:
        list_jobs()
        return
    
    # 检查依赖
    if args.check:
        check_dependencies()
        return
    
    # 检查依赖
    if not check_dependencies():
        return
    
    # 启动指定作业
    if args.job:
        run_job(args.job)
        return
    
    # 启动所有作业
    if args.all:
        run_all_jobs()
        return
    
    # 默认显示帮助
    parser.print_help()
    print()
    list_jobs()


if __name__ == "__main__":
    main()

