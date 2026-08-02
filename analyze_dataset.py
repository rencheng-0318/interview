"""Analyze the seed dataset to quantify patient-document distribution for strategy selection."""

import csv
from collections import Counter, defaultdict

# Read patients
patient_practice = {}
with open("database/seed/data/patients.csv", "r") as f:
    reader = csv.DictReader(f)
    for row in reader:
        patient_practice[row["id"]] = {
            "practice_id": row["practice_id"],
            "name": f"{row['first_name']} {row['last_name']}",
        }

# Read documents
patient_docs = defaultdict(list)
doc_types_count = Counter()
practice_doc_types = defaultdict(Counter)

with open("database/seed/data/clinical_documents.csv", "r") as f:
    reader = csv.DictReader(f)
    for row in reader:
        pid = row["patient_id"]
        patient_docs[pid].append({
            "document_id": row["id"],
            "document_type": row["document_type"],
            "title": row["title"],
        })
        doc_types_count[row["document_type"]] += 1
        practice_doc_types[row["practice_id"]][row["document_type"]] += 1

# Statistics
total_patients = len(patient_practice)
total_documents = sum(len(docs) for docs in patient_docs.values())
docs_per_patient = [len(docs) for docs in patient_docs.values()]

print("=" * 80)
print("📊 DATASET STATISTICS FOR STRATEGY SELECTION")
print("=" * 80)

print(f"\n📋 BASIC COUNTS:")
print(f"   Total patients: {total_patients}")
print(f"   Total documents: {total_documents}")
print(f"   Average docs per patient: {total_documents / total_patients:.2f}")

print(f"\n📈 DOCS PER PATIENT DISTRIBUTION:")
dist = Counter(docs_per_patient)
for k in sorted(dist.keys()):
    percentage = dist[k] / total_patients * 100
    print(f"   {k:3d} documents: {dist[k]:4d} patients ({percentage:5.1f}%)")

print(f"\n   Percentiles:")
sorted_docs = sorted(docs_per_patient)
for p in [50, 75, 90, 95, 99]:
    idx = int(len(sorted_docs) * p / 100)
    print(f"     P{p}: {sorted_docs[idx]} documents")

print(f"\n🔤 DOCUMENT TYPE DISTRIBUTION:")
for doc_type, count in doc_types_count.most_common():
    percentage = count / total_documents * 100
    print(f"   {doc_type:25s}: {count:5d} ({percentage:5.1f}%)")

print(f"\n🏥 PRACTICE BREAKDOWN:")
practices = defaultdict(lambda: {"patients": set(), "documents": 0})
for pid, info in patient_practice.items():
    practices[info["practice_id"]]["patients"].add(pid)
    practices[info["practice_id"]]["documents"] += len(patient_docs.get(pid, []))

for practice_id, stats in sorted(practices.items()):
    avg_docs = stats["documents"] / len(stats["patients"]) if stats["patients"] else 0
    print(f"   {practice_id:20s}: {len(stats['patients']):4d} patients, {stats['documents']:5d} documents (avg {avg_docs:.2f} docs/patient)")

print(f"\n🎯 CANDIDATE MULTIPLIER ANALYSIS:")
print(f"   If user requests limit=10 different patients:")
for multiplier in [3, 4, 5, 6, 8, 10]:
    candidate_limit = 10 * multiplier
    
    # Simulate: how many unique patients do we get with top candidate_limit chunks?
    # This is an upper bound (assuming best-case distribution)
    print(f"   ×{multiplier} → candidate_limit={candidate_limit:3d} → ")
    
    # Estimate: if average is 3.36 docs/patient, then:
    # - With 50 candidates, we can cover ~50/3.36 ≈ 14.9 different patients (theoretical max)
    # - But actual depends on variance
    
    # Use percentile data to estimate
    p95_docs = sorted_docs[int(len(sorted_docs) * 0.95)]
    p99_docs = sorted_docs[int(len(sorted_docs) * 0.99)]
    
    estimated_patients = candidate_limit / avg_docs
    print(f"            Theoretical max unique patients: {estimated_patients:.1f}")
    print(f"            P95 patient has {p95_docs} docs, P99 has {p99_docs} docs")

print(f"\n💡 RECOMMENDED MULTIPLIER:")
avg_multiplier = total_documents / total_patients
print(f"   Actual ratio: {avg_multiplier:.2f}")
print(f"   Recommended (with safety factor 1.5x): {avg_multiplier * 1.5:.1f} → **5×**")
print(f"   Reasoning: Covers average case + safety margin for variance")

print(f"\n⚠️ EDGE CASES:")
max_docs = max(docs_per_patient)
max_patient = [pid for pid, docs in patient_docs.items() if len(docs) == max_docs][0]
print(f"   Max docs for single patient: {max_docs} ({patient_practice[max_patient]['name']})")
print(f"   If we search ×5 and all match same patient: lose {5 - 1} slots")

print(f"\n📦 SNIPPET LENGTH ANALYSIS:")
chunk_lengths = []
with open("database/seed/data/clinical_documents.csv", "r") as f:
    reader = csv.DictReader(f)
    for row in reader:
        chunk_lengths.append(len(row["body"]))

print(f"   Chunk (document body) length statistics:")
print(f"   Min: {min(chunk_lengths)} characters")
print(f"   Max: {max(chunk_lengths)} characters")
print(f"   Mean: {sum(chunk_lengths) / len(chunk_lengths):.0f} characters")
print(f"   Median: {sorted(chunk_lengths)[len(sorted(chunk_lengths))//2]} characters")

p90 = sorted(chunk_lengths)[int(len(chunk_lengths) * 0.90)]
p95 = sorted(chunk_lengths)[int(len(chunk_lengths) * 0.95)]
print(f"   P90: {p90} characters")
print(f"   P95: {p95} characters")

print(f"\n   If we truncate to 300 chars:")
under_300 = sum(1 for l in chunk_lengths if l <= 300)
under_500 = sum(1 for l in chunk_lengths if l <= 500)
print(f"   Naturally ≤300 chars: {under_300}/{len(chunk_lengths)} ({under_300/len(chunk_lengths)*100:.1f}%)")
print(f"   Naturally ≤500 chars: {under_500}/{len(chunk_lengths)} ({under_500/len(chunk_lengths)*100:.1f}%)")

print("\n" + "=" * 80)
