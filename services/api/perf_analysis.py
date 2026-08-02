"""Performance analysis script for clinical search."""
import asyncio
import time
import sys
import httpx
import asyncpg


async def analyze_performance():
    # Connect to database
    conn = await asyncpg.connect(
        host="db",
        database="clinical_search",
        user="clinical",
        password="local_dev_only"
    )
    
    query_text = "chest pain"
    
    print("=" * 70)
    print("临床搜索性能分析")
    print("=" * 70)
    print(f"\n查询: \"{query_text}\"")
    total_chunks = await conn.fetchval('SELECT count(*) FROM document_chunks')
    northside_chunks = await conn.fetchval('SELECT count(*) FROM document_chunks WHERE practice_id = $1', 'northside')
    print(f"总数据量: {total_chunks} chunks")
    print(f"Northside数据量: {northside_chunks} chunks\n")
    
    # Get a real embedding vector
    embedding_sql = "SELECT embedding FROM document_chunks WHERE patient_id = 'P0001' LIMIT 1"
    test_vec = await conn.fetchval(embedding_sql)
    
    # Step 1: Embedding service call time
    print("【步骤1】Embedding服务调用")
    import httpx
    started = time.perf_counter()
    async with httpx.AsyncClient(timeout=30) as http_client:
        resp = await http_client.post("http://embedding:8080/v1/embeddings",
                                      json={"texts": [query_text]})
        embedding_data = resp.json()
        query_vector = embedding_data["embeddings"][0]
    embedding_time = (time.perf_counter() - started) * 1000
    print(f"  向量化耗时: {embedding_time:.2f}ms")
    print(f"  Vector维度: {len(query_vector)}\n")
    
    # Step 2: HNSW vector search (minimal columns)
    print("【步骤2】HNSW向量搜索 (仅patient_id + score)")
    vector_sql = """
        SELECT dc.patient_id, 
               1 - (dc.embedding <=> $1::vector) AS relevance_score
        FROM document_chunks dc  
        WHERE dc.practice_id = $2
        ORDER BY dc.embedding <=> $1::vector
        LIMIT 50
    """
    
    started = time.perf_counter()
    rows_simple = await conn.fetch(vector_sql, query_vector, "northside")
    hnsw_time = (time.perf_counter() - started) * 1000
    print(f"  HNSW索引扫描: {hnsw_time:.2f}ms")
    print(f"  返回行数: {len(rows_simple)}\n")
    
    # Step 3: Full search with JOINs
    print("【步骤3】完整查询 (含JOIN patients + clinical_documents)")
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
    
    started = time.perf_counter()
    rows_full = await conn.fetch(full_sql, query_vector, "northside")
    join_time = (time.perf_counter() - started) * 1000
    print(f"  含JOIN查询: {join_time:.2f}ms")
    print(f"  相比纯向量增加: {join_time - hnsw_time:.2f}ms\n")
    
    # Step 4: Patient aggregation
    print("【步骤4】患者级聚合")
    started = time.perf_counter()
    
    patient_map: dict[str, dict] = {}
    for row in rows_full:
        pid = row["patient_id"]
        score = float(row["relevance_score"])
        if score > patient_map.get(pid, {}).get("relevance_score", -1.0):
            if pid not in patient_map:
                patient_map[pid] = {
                    "patient_id": pid,
                    "display_name": row["display_name"],
                    "document_id": row["document_id"],
                    "document_type": row["document_type"],
                    "document_title": row["document_title"],
                    "document_date": str(row["document_date"]),
                    "snippet": row["content"][:300] + "..." if len(row["content"]) > 300 else row["content"],
                    "relevance_score": score,
                    "_doc_ids": {row["document_id"]},
                }
            else:
                pm = patient_map[pid]
                pm["_doc_ids"].add(row["document_id"])
                pm["relevance_score"] = score
                pm["document_id"] = row["document_id"]
                pm["document_type"] = row["document_type"]
                pm["document_title"] = row["document_title"]
                pm["document_date"] = str(row["document_date"])
                pm["snippet"] = row["content"][:300] + "..." if len(row["content"]) > 300 else row["content"]

    results = []
    for data in patient_map.values():
        doc_count = len(data.pop("_doc_ids"))
        results.append({
            **data,
            "additional_matching_documents": max(0, doc_count - 1),
        })
    
    results.sort(key=lambda r: r["relevance_score"], reverse=True)
    results = results[:10]
    
    aggregation_time = (time.perf_counter() - started) * 1000
    print(f"  聚合处理时间: {aggregation_time:.2f}ms")
    print(f"  聚合前chunks: {len(rows_full)}")
    print(f"  聚合后patients: {len(results)}\n")
    
    # Step 5: JSON serialization
    print("【步骤5】JSON序列化")
    import json
    started = time.perf_counter()
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
    } for r in results]
    json_str = json.dumps(json_data, ensure_ascii=False, default=str)
    serialization_time = (time.perf_counter() - started) * 1000
    print(f"  JSON序列化: {serialization_time:.2f}ms")
    print(f"  JSON大小: {len(json_str)} bytes\n")
    
    # Step 6: BM25 comparison
    print("【步骤6】BM25全文搜索 (降级方案对比)")
    bm25_sql = """
        SELECT dc.patient_id,
               ts_rank(dc.content_tsv, plainto_tsquery('english', $1)) AS relevance_score
        FROM document_chunks dc
        WHERE dc.content_tsv @@ plainto_tsquery('english', $1)
          AND dc.practice_id = $2
        ORDER BY relevance_score DESC
        LIMIT 50
    """
    started = time.perf_counter()
    bm25_rows = await conn.fetch(bm25_sql, query_text, "northside")
    bm25_time = (time.perf_counter() - started) * 1000
    print(f"  BM25查询: {bm25_time:.2f}ms")
    print(f"  返回行数: {len(bm25_rows)}\n")
    
    # Summary
    total_time = embedding_time + join_time + aggregation_time + serialization_time
    
    print("=" * 70)
    print("时间分布总结 (非缓存查询)")
    print("=" * 70)
    print(f"  Embedding调用:     {embedding_time:>8.2f}ms  ({embedding_time/total_time*100:>5.1f}%)")
    print(f"  数据库查询(JOIN):  {join_time:>8.2f}ms  ({join_time/total_time*100:>5.1f}%)")
    print(f"  患者聚合:          {aggregation_time:>8.2f}ms  ({aggregation_time/total_time*100:>5.1f}%)")
    print(f"  JSON序列化:        {serialization_time:>8.2f}ms  ({serialization_time/total_time*100:>5.1f}%)")
    print(f"  {'':>25}")
    print(f"  总计:              {total_time:>8.2f}ms")
    print("=" * 70)
    
    # Optimization suggestions
    print("\n【优化建议】")
    bottlenecks = []
    
    if embedding_time > 100:
        bottlenecks.append(f"1. Embedding服务是主要瓶颈 ({embedding_time:.0f}ms)")
        bottlenecks.append("   → 启用embedding缓存可避免重复计算")
        bottlenecks.append("   → 当前缓存已开启，非首次查询会快很多")
    
    if join_time > 50:
        bottlenecks.append(f"2. 数据库JOIN开销较大 ({join_time:.0f}ms)")
        bottlenecks.append("   → 策略1: 先检索document_id，然后分批JOIN减少数据传输")
        bottlenecks.append("   → 策略2: 使用子查询替代多表JOIN")
        bottlenecks.append("   → 策略3: 考虑冗余存储常用字段避免JOIN")
    
    if aggregation_time > 30:
        bottlenecks.append(f"3. 患者聚合需要优化 ({aggregation_time:.0f}ms)")
        bottlenecks.append("   → 改用SQL层聚合 (GROUP BY + WINDOW FUNCTIONS)")
        bottlenecks.append("   → 使用orjson替代json模块加速序列化")
    
    print("\n关键发现:")
    if embedding_time > join_time:
        print(f"  ✓ Embedding调用时间 > 数据库查询时间")
        print(f"  ✓ 优化重点应放在embedding层（缓存、批处理）")
    else:
        print(f"  ✓ 数据库查询是主要瓶颈")
        print(f"  ✓ 需要考虑查询优化和索引调整")
    
    await conn.close()


if __name__ == "__main__":
    asyncio.run(analyze_performance())
