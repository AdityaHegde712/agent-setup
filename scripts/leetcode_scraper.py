import sys
import json
import requests
from leetscrape import GetQuestion


def get_raw_graphql_details(title_slug: str) -> dict:
    """Fetch additional details (code snippets for all languages, sample test cases)

    directly from LeetCode's GraphQL API.
    """
    url = "https://leetcode.com/graphql"
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            " (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ),
        "Content-Type": "application/json",
    }
    query = """
    query questionData($titleSlug: String!) {
        question(titleSlug: $titleSlug) {
            codeSnippets {
                lang
                langSlug
                code
            }
            sampleTestCase
        }
    }
    """
    try:
        response = requests.post(
            url,
            json={"query": query, "variables": {"titleSlug": title_slug}},
            headers=headers,
            timeout=10,
        )
        if response.status_code == 200:
            return response.json().get("data", {}).get("question", {}) or {}
    except Exception:
        pass
    return {}


def scrape_question(title_slug: str) -> dict:
    """Scrapes LeetCode question details using a combination of leetscrape

    and raw GraphQL queries.
    """
    if not title_slug:
        raise ValueError("Title slug cannot be empty.")

    # 1. Scrape using leetscrape GetQuestion
    scraper = GetQuestion(titleSlug=title_slug)
    try:
        question_data = scraper.scrape()
    except Exception as e:
        raise RuntimeError(
            f"Failed to scrape question '{title_slug}' via leetscrape: {e}"
        )

    # 2. Fetch additional snippets & sample test case via GraphQL
    extra_details = get_raw_graphql_details(title_slug)

    # Combine results
    code_snippets = extra_details.get("codeSnippets", [])
    sample_test_case = extra_details.get("sampleTestCase", "")

    # Fallback to leetscrape's parsed python stub if GraphQL extra failed or was empty
    if not code_snippets and question_data.Code:
        code_snippets = [
            {"lang": "Python3", "langSlug": "python3", "code": question_data.Code}
        ]

    return {
        "titleSlug": title_slug,
        "title": question_data.title,
        "difficulty": question_data.difficulty,
        "qid": question_data.QID,
        "content": question_data.Body,
        "hints": question_data.Hints,
        "isPaidOnly": question_data.isPaidOnly,
        "codeSnippets": code_snippets,
        "sampleTestCase": sample_test_case,
    }


def main():
    if len(sys.argv) < 2:
        print(
            json.dumps({"error": "No titleSlug provided. Usage: python scraper.py <titleSlug>"})
        )
        sys.exit(1)

    slug = sys.argv[1].strip()
    try:
        data = scrape_question(slug)
        print(json.dumps(data, indent=2))
    except Exception as e:
        print(json.dumps({"error": str(e)}))
        sys.exit(1)


if __name__ == "__main__":
    main()
