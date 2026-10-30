from unittest import mock

from app.vector_store.s3_vectors import S3VectorsStore


def test_put_sends_float32_records():
    client = mock.MagicMock()
    with mock.patch("boto3.client", return_value=client):
        store = S3VectorsStore(bucket="bucket", index="index", dimension=3)

    store.put(["k1"], [[1.0, 2.0, 3.0]], [{"text": "hello"}])

    call = client.put_vectors.call_args
    assert call.kwargs["vectorBucketName"] == "bucket"
    assert call.kwargs["indexName"] == "index"
    record = call.kwargs["vectors"][0]
    assert record["key"] == "k1"
    assert record["data"] == {"float32": [1.0, 2.0, 3.0]}
    assert record["metadata"] == {"text": "hello"}


def test_search_parses_metadata_and_distance():
    client = mock.MagicMock()
    client.query_vectors.return_value = {
        "vectors": [{"key": "k1", "distance": 0.2, "metadata": '{"text": "hi"}'}]
    }
    with mock.patch("boto3.client", return_value=client):
        store = S3VectorsStore(bucket="bucket", index="index", dimension=3, distance="cosine")

    results = store.search([1.0, 0.0, 0.0], top_k=4)

    assert len(results) == 1
    assert results[0].id == "k1"
    assert results[0].score == 0.2
    assert results[0].payload == {"text": "hi"}
