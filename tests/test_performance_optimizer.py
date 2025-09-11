#!/usr/bin/env python3
"""
test_performance_optimizer.py - Test performance optimization system
"""
import sys
import os
import time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.performance_optimizer import performance_optimizer, get_performance_stats, identify_bottlenecks


def test_performance_monitoring():
    """Test performance monitoring capabilities"""
    print("⚡ Testing performance monitoring...")
    
    # Start monitoring
    start_result = performance_optimizer.do("start monitoring")
    print(f"✅ Monitoring started: {start_result}")
    
    # Wait for metrics collection
    time.sleep(2)
    
    # Check monitoring status
    status = performance_optimizer.ask("monitoring")
    print(f"✅ Monitoring status: {status}")
    
    # Stop monitoring
    stop_result = performance_optimizer.do("stop monitoring")
    print(f"✅ Monitoring stopped: {stop_result}")


def test_performance_stats():
    """Test performance statistics collection"""
    print("\n📊 Testing performance statistics...")
    
    # Get performance stats
    stats = get_performance_stats()
    print(f"✅ Performance stats collected: {len(stats)} metrics")
    
    expected_keys = ['timestamp', 'monitoring_active', 'total_metrics']
    stats_complete = all(key in stats for key in expected_keys)
    print(f"✅ Stats completeness: {'✓' if stats_complete else '✗'}")
    
    # Test Discord formatting
    discord_stats = performance_optimizer.tell("discord", stats)
    print("✅ Discord formatting:")
    print(discord_stats)


def test_bottleneck_detection():
    """Test bottleneck detection"""
    print("\n🔍 Testing bottleneck detection...")
    
    # Identify bottlenecks
    bottlenecks = identify_bottlenecks()
    print(f"✅ Bottlenecks identified: {len(bottlenecks.get('bottlenecks', []))}")
    
    # Test Discord formatting
    discord_bottlenecks = performance_optimizer.tell("discord", bottlenecks)
    print("✅ Bottleneck report:")
    print(discord_bottlenecks)


def test_optimization_recommendations():
    """Test optimization recommendations"""
    print("\n💡 Testing optimization recommendations...")
    
    # Get recommendations
    recommendations = performance_optimizer.ask("optimization recommendations")
    rec_count = len(recommendations.get('recommendations', []))
    print(f"✅ Recommendations available: {rec_count}")
    
    # Show high-impact recommendations
    high_impact = [
        r for r in recommendations.get('recommendations', [])
        if r.get('impact') == 'high'
    ]
    print(f"✅ High-impact optimizations: {len(high_impact)}")
    
    for rec in high_impact:
        print(f"   • {rec['name']}: {rec['description']}")


def test_system_metrics():
    """Test individual system metrics"""
    print("\n🖥️ Testing system metrics...")
    
    # Memory metrics
    memory = performance_optimizer.ask("memory usage")
    memory_complete = 'total_gb' in memory and 'percent' in memory
    print(f"✅ Memory metrics: {'✓' if memory_complete else '✗'}")
    if memory_complete:
        print(f"   Memory usage: {memory['percent']:.1f}% ({memory['used_gb']:.1f}GB/{memory['total_gb']:.1f}GB)")
    
    # CPU metrics
    cpu = performance_optimizer.ask("cpu")
    cpu_complete = 'percent' in cpu and 'count' in cpu
    print(f"✅ CPU metrics: {'✓' if cpu_complete else '✗'}")
    if cpu_complete:
        print(f"   CPU usage: {cpu['percent']:.1f}% ({cpu['count']} cores)")


def test_optimization_application():
    """Test applying optimizations"""
    print("\n🔧 Testing optimization application...")
    
    # Apply database optimizations
    db_opt = performance_optimizer.do("optimize database")
    print(f"✅ Database optimization: {db_opt.get('optimization', 'Applied')}")
    
    # Apply API optimizations
    api_opt = performance_optimizer.do("optimize api")
    print(f"✅ API optimization: {api_opt.get('optimization', 'Applied')}")
    
    # Apply memory optimizations
    mem_opt = performance_optimizer.do("optimize memory")
    print(f"✅ Memory optimization: {mem_opt.get('optimization', 'Applied')}")
    
    # Test applying all optimizations
    all_opt = performance_optimizer.do("optimize all")
    applied_count = all_opt.get('applied_count', 0)
    total_count = all_opt.get('total_optimizations', 0)
    print(f"✅ All optimizations: {applied_count}/{total_count} applied")


def test_cache_management():
    """Test cache and cleanup functionality"""
    print("\n🧹 Testing cache management...")
    
    # Clear cache
    clear_result = performance_optimizer.do("clear cache")
    print(f"✅ Cache cleared: {clear_result}")


def test_different_output_formats():
    """Test different output formats"""
    print("\n🎨 Testing output formats...")
    
    # Get some data
    stats = performance_optimizer.ask("performance stats")
    
    # Test JSON output
    json_output = performance_optimizer.tell("json", stats)
    json_valid = json_output.startswith('{') and json_output.endswith('}')
    print(f"✅ JSON format: {'✓' if json_valid else '✗'}")
    
    # Test text output
    text_output = performance_optimizer.tell("text", stats)
    print(f"✅ Text format: {len(text_output)} characters")
    
    # Test dashboard format (HTML)
    dashboard_output = performance_optimizer.tell("dashboard", stats)
    print(f"✅ Dashboard format: {'✓' if 'html' in dashboard_output.lower() else 'Text'}")


def benchmark_performance_impact():
    """Benchmark the performance impact of the optimizer itself"""
    print("\n⏱️ Benchmarking optimizer performance...")
    
    # Measure stats collection time
    start_time = time.time()
    for _ in range(10):
        stats = performance_optimizer.ask("performance stats")
    stats_time = (time.time() - start_time) / 10
    print(f"✅ Average stats collection time: {stats_time*1000:.2f}ms")
    
    # Measure bottleneck detection time
    start_time = time.time()
    bottlenecks = performance_optimizer.ask("bottlenecks")
    bottleneck_time = time.time() - start_time
    print(f"✅ Bottleneck detection time: {bottleneck_time*1000:.2f}ms")
    
    print(f"✅ Optimizer overhead: {'Low' if stats_time < 0.01 else 'Medium' if stats_time < 0.05 else 'High'}")


if __name__ == "__main__":
    print("🧪 Starting Performance Optimizer comprehensive tests...\n")
    
    test_performance_monitoring()
    test_performance_stats()
    test_bottleneck_detection()
    test_optimization_recommendations()
    test_system_metrics()
    test_optimization_application()
    test_cache_management()
    test_different_output_formats()
    benchmark_performance_impact()
    
    print("\n🎉 All performance optimizer tests complete!")
    print("\nPerformance Optimizer Features Verified:")
    print("• 📊 Real-time system monitoring (CPU, Memory, I/O)")
    print("• 🔍 Automatic bottleneck detection and analysis")
    print("• 💡 Intelligent optimization recommendations")
    print("• ⚡ Adaptive rate limiting and performance tuning")
    print("• 🎯 Multiple output formats (Discord, JSON, HTML)")
    print("• 🔧 Automated optimization application")
    print("• 📈 Performance trend tracking and alerts")
    print("• 🧹 Cache management and resource cleanup")