"""Detailed performance profiling for clinical search query."""
import asyncio
import time
import sys
import httpx
import asyncpg
from datetime import datetime


class Timer:
    """Simple timer for measuring durations."""
    def __init__(self):
        self.phases = []
        self._start = None
    
    def start(self, name: str):
        self._start = time.perf_counter()
        self._name = name
    
    def stop(self) -> float:
        if self._start is None:
            return 0.0
        duration = (time.perf_counter() - self._start) * 1000
        self.phases.append((self._name, duration))
        self._start = None
        return duration


async def profile_query():
    timer = Timer()
    
    # Connect to database
    print("=" * 80)
    print("临床搜索查询性能剖析 - 详细版")
    print("=" * 80)
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    conn = await asyncpg.connect(
        host="db",
        database="clinical_search",
        user="clinical",
        password="local_dev_only"
    )
    
    query_text = "chest pain"  # 测试查询
    
    # Embedding service URL from environment
    import os
    os.environ["EMBEDDING_SERVICE_URL"] = "http://embedding:8080"
    embedding_url = os.getenv("EMBEDDING_SERVICE_URL", "http://embedding:8080")
    
    # === Phase 1: Embedding Call ===
    print("📊 Phase 1: Embedding 向量化")
    print("-" * 80)
    timer.start("embedding_call")
    
    async with httpx.AsyncClient(timeout=30) as http_client:
        resp = await http_client.post(
            f"{embedding_url}/v1/embeddings",
            json={"texts": [query_text]}
        )
        embedding_data = resp.json()
        query_vector = embedding_data["embeddings"][0]
    
    embedding_time = timer.stop()
    print(f"   ✅ 耗时: {embedding_time:.2f}ms")
    print(f"   📐 向量维度: {len(query_vector)}")
    print()
    
    # === Phase 2: Database Query Execution ===
    print("📊 Phase 2: 数据库查询执行")
    print("-" * 80)
    
    # 2a: HNSW Vector Search (pure vector, minimal columns)
    vector_sql_minimal = """
        SELECT dc.patient_id, 
               1 - (dc.embedding <=> $1::vector) AS relevance_score
        FROM document_chunks dc  
        WHERE dc.practice_id = $2
        ORDER BY dc.embedding <=> $1::vector
        LIMIT 50
    """
    
    timer.start("hnsw_vector_search")
    rows_minimal = await conn.fetch(vector_sql_minimal, query_vector, "northside")
    hnsw_time = timer.stop()
    
    print(f"   🔹 HNSW向量检索 (仅patient_id + score): {hnsw_time:.2f}ms")
    print(f"   📊 返回chunks数: {len(rows_minimal)}")
    
    # 2b: Full Query with JOINs
    full_sql = """
        SELECT dc.patient_id,
               p.first_name || ' ' || p.last_name AS display_name,
               dc.document_id, dc.document_type,
               cd.title AS document_title, cd.document_date,
               dc.content,
               1 - (dc.embedding <=> $1::vector) AS relevance_score
        FROM document_chunks dc
        JOIN patients p ON p.id = dc.patient_id
        JOIN clinical_documents cd ON cd.id = dc.document_id
        WHERE dc.practice_id = $2
        ORDER BY dc.embedding <=> $1::vector
        LIMIT 50
    """
    
    timer.start("full_join_query")
    rows_full = await conn.fetch(full_sql, query_vector, "northside")
    join_time = timer.stop()
    
    print(f"   🔹 完整JOIN查询:                          {join_time:.2f}ms")
    print(f"   🔹 JOIN额外开销:                           {join_time - hnsw_time:.2f}ms")
    print(f"   📊 返回rows数: {len(rows_full)}")
    
    # Analyze JOIN cost distribution
    if join_time > 0 and hnsw_time > 0:
        join_overhead_pct = (join_time - hnsw_time) / join_time * 100
        print(f"   💡 HNSW占比: {hnsw_time/join_time*100:.1f}%, JOIN占比: {join_overhead_pct:.1f}%")
    print()
    
    # === Phase 3: Result Processing ===
    print("📊 Phase 3: 结果处理 (Python层)")
    print("-" * 80)
    
    timer.start("dict_conversion")
    rows_dict = [dict(r) for r in rows_full]
    dict_time = timer.stop()
    print(f"   🔹 Record转dict:       {dict_time:.2f}ms ({len(rows_dict)} records)")
    
    timer.start("patient_aggregation")
    from app.features.search.service import _aggregate_patients
    patient_results = _aggregate_patients(rows_dict)
    aggregation_time = timer.stop()
    print(f"   🔹 患者级聚合:         {aggregation_time:.2f}ms")
    print(f"   📊 聚合前: {len(rows_full)} chunks → 聚合后: {len(patient_results)} patients")
    
    timer.start("limiting")
    patient_results = patient_results[:10]
    limiting_time = timer.stop()
    print(f"   🔹 截取前10条:         {limiting_time:.2f}ms")
    print()
    
    # === Phase 4: JSON Serialization ===
    print("📊 Phase 4: JSON 序列化")
    print("-" * 80)
    
    timer.start("model_conversion")
    from app.features.search.schemas import (
        ClinicalSearchResponse, SearchResult, PatientSummary, 
        BestMatch, SearchMeta
    )
    
    results = [
        SearchResult(
            patient=PatientSummary(id=r["patient_id"], display_name=r["display_name"]),
            best_match=BestMatch(
                document_id=r["document_id"],
                document_type=r["document_type"],
                document_title=r["document_title"],
                document_date=r["document_date"],
                snippet=r["snippet"],
                relevance_score=r["relevance_score"],
            ),
            additional_matching_documents=r["additional_matching_documents"],
        )
        for r in patient_results
    ]
    model_time = timer.stop()
    print(f"   🔹 Pydantic模型构建:  {model_time:.2f}ms")
    
    timer.start("json_dump")
    # Simulate FastAPI's json serialization
    import json
    json_data = [{
        "patient": {"id": r["patient_id"], "display_name": r["display_name"]},
        "best_match": {
            "document_id": r["document_id"],
            "document_type": r["document_type"],
            "document_title": r["document_title"],
            "relevance_score": r["relevance_score"],
            "snippet": r["snippet"],
        },
        "additional_matching_documents": r["additional_matching_documents"],
    } for r in patient_results]
    json_str = json.dumps(json_data, ensure_ascii=False, default=str)
    serialization_time = timer.stop()
    print(f"   🔹 JSON序列化:        {serialization_time:.2f}ms")
    print(f"   📦 JSON大小:          {len(json_str)} bytes")
    print()
    
    # === Phase 5: Network/Overhead ===
    print("📊 Phase 5: 网络传输与开销")
    print("-" * 80)
    
    # Measure network roundtrip for DB
    timer.start("db_roundtrip_single")
    await conn.fetchval("SELECT 1")
    db_network_base = timer.stop()
    print(f"   🔹 数据库基础RTT:     {db_network_base:.2f}ms (单次查询)")
    
    # Measure HTTP to embedding service
    timer.start("embedding_network")
    async with httpx.AsyncClient(timeout=5) as http_client:
        await http_client.post(
            f"{embedding_url}/v1/embeddings",
            json={"texts": ["test"]}
        )
    embedding_network = timer.stop()
    print(f"   🔹 Embedding网络RTT:  {embedding_network:.2f}ms")
    print()
    
    # Close connection
    await conn.close()
    
    # === Summary Report ===
    total_time = sum(t for _, t in timer.phases)
    
    print("=" * 80)
    print("📈 性能分析总结")
    print("=" * 80)
    print()
    print(f"{'阶段':<30} {'耗时(ms)':>12} {'占比':>10} {'累积':>12}")
    print("-" * 80)
    
    cumulative = 0
    for phase_name, phase_time in timer.phases:
        cumulative += phase_time
        pct = phase_time / total_time * 100 if total_time > 0 else 0
        print(f"{phase_name:<30} {phase_time:>11.2f} {pct:>9.1f}% {cumulative:>11.2f}ms")
    
    print("-" * 80)
    print(f"{'总计':<30} {total_time:>11.2f} {100.0:>9.1f}%")
    print("=" * 80)
    print()
    
    # Bottleneck analysis
    print("🔍 瓶颈分析:")
    print("-" * 80)
    
    phases = dict(timer.phases)
    
    if phases.get("embedding_call", 0) > phases.get("full_join_query", 0):
        print("  ⚠️  【主要瓶颈】Embedding服务调用")
        print(f"      耗时: {phases.get('embedding_call', 0):.2f}ms")
        print("      建议:")
        print("      - 启用embedding缓存 (已启用)")
        print("      - 考虑本地小模型做热缓存")
        print("      - 或增加预计算查询向量池")
    else:
        print("  ⚠️  【主要瓶颈】数据库查询")
        print(f"      耗时: {phases.get('full_join_query', 0):.2f}ms")
        print("      建议:")
        print("      - 检查HNSW索引效率")
        print("      - 优化JOIN操作")
        print("      - 考虑冗余存储常用字段")
    
    if phases.get("patient_aggregation", 0) > 50:
        print()
        print("  ⚠️  【次要瓶颈】患者聚合逻辑")
        print(f"      耗时: {phases.get('patient_aggregation', 0):.2f}ms")
        print("      建议:")
        print("      - 使用SQL窗口函数部分聚合")
        print("      - 优化Python字典操作")
    
    print()
    print("=" * 80)
    print("💡 优化建议优先级:")
    print("=" * 80)
    
    if phases.get("embedding_call", 0) > 200:
        print("1. 🔴 HIGH - Embedding调用优化 (当前{}ms)".format(phases.get("embedding_call", 0)))
        print("   目标: <100ms (通过缓存或本地模型)")
    
    if phases.get("full_join_query", 0) > 100:
        print("2. 🟡 MEDIUM - 数据库查询优化 (当前{}ms)".format(phases.get("full_join_query", 0)))
        print("   目标: <50ms (索引优化、减少JOIN)")
    
    if phases.get("patient_aggregation", 0) > 30:
        print("3. 🟢 LOW - 聚合逻辑优化 (当前{}ms)".format(phases.get("patient_aggregation", 0)))
        print("   目标: <20ms (算法优化)")
    
    print()


if __name__ == "__main__":
    asyncio.run(profile_query())
