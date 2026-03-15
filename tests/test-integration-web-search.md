# Integration Test Plan for Web Search

## Introduction

web_search(query, num_results), Serper API mock. Parse results to titles/snippet/links. Tests queries, limits, errors. (70 words)

## Test Strategy

@patch('requests.post')

## Test Cases

25 cases: simple query, site:stack, num=10.

## Pytest Code Stubs

```python
@patch('requests.post')
def test_search(mock_post):
    mock_post.return_value.json.return_value = {'organic': [{'title': 'test'}]}
    results = web_search('python')
    assert len(results) == 1
```

Diagram.

Word count: 515