# -*- coding: utf-8 -*-

import os
import re
import shutil
import json
import sys
import requests


# ============================================================
# UTF-8
# ============================================================

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except AttributeError:
    pass


# ============================================================
# CONFIGURATION
# ============================================================

INCOMING_FOLDER = "incoming"
SOLUTIONS_FOLDER = "solutions"
DATA_FILE = os.path.join("data", "problems.json")

LEETCODE_URL = "https://leetcode.com/graphql/"


# ============================================================
# LEETCODE METADATA
# ============================================================

def get_leetcode_problem(problem_number):

    query = """
    query problemsetQuestionList(
        $categorySlug: String,
        $limit: Int,
        $skip: Int,
        $filters: QuestionListFilterInput
    ) {
        problemsetQuestionList: questionList(
            categorySlug: $categorySlug
            limit: $limit
            skip: $skip
            filters: $filters
        ) {
            total: totalNum
            questions: data {
                frontendQuestionId: questionFrontendId
                title
                titleSlug
                difficulty
                topicTags {
                    name
                    slug
                }
            }
        }
    }
    """

    variables = {
        "categorySlug": "",
        "skip": 0,
        "limit": 10,
        "filters": {
            "searchKeywords": str(problem_number)
        }
    }

    payload = {
        "operationName": "problemsetQuestionList",
        "query": query,
        "variables": variables
    }

    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0",
        "Referer": "https://leetcode.com/problemset/"
    }

    try:

        response = requests.post(
            LEETCODE_URL,
            json=payload,
            headers=headers,
            timeout=20
        )

        print(
            f"   HTTP Status: {response.status_code}"
        )

        response.raise_for_status()

        data = response.json()

        # Check GraphQL errors
        if "errors" in data:

            print()
            print("❌ LeetCode GraphQL returned an error:")

            for error in data["errors"]:
                print(
                    "   ",
                    error.get("message", error)
                )

            return None

        question_list = (
            data
            .get("data", {})
            .get("problemsetQuestionList", {})
        )

        questions = question_list.get(
            "questions",
            []
        )

        # Find exact problem number
        for question in questions:

            if str(
                question.get("frontendQuestionId")
            ) == str(problem_number):

                return question

        print()
        print(
            f"❌ Problem #{problem_number} "
            "was not found in the returned results."
        )

        return None

    except requests.exceptions.RequestException as e:

        print()
        print("❌ Could not connect to LeetCode.")
        print(e)

        return None

    except json.JSONDecodeError:

        print()
        print("❌ LeetCode returned invalid JSON.")

        print(
            response.text[:500]
        )

        return None

    except Exception as e:

        print()
        print("❌ Unexpected error:")
        print(e)

        return None


# ============================================================
# LOAD PROBLEMS
# ============================================================

def load_problems():

    if not os.path.exists(DATA_FILE):
        return []

    try:

        with open(
            DATA_FILE,
            "r",
            encoding="utf-8"
        ) as file:

            return json.load(file)

    except Exception:

        return []


# ============================================================
# SAVE PROBLEMS
# ============================================================

def save_problems(problems):

    os.makedirs(
        "data",
        exist_ok=True
    )

    with open(
        DATA_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            problems,
            file,
            indent=4,
            ensure_ascii=False
        )


# ============================================================
# CREATE SAFE FILE NAME
# ============================================================

def create_safe_filename(name):

    name = re.sub(
        r"[^a-zA-Z0-9]+",
        "-",
        name
    )

    return name.strip("-")


# ============================================================
# EXTRACT PROBLEM NUMBER
# ============================================================

def extract_problem_number(filename):

    match = re.match(
        r"^(\d+)",
        filename
    )

    if match:
        return match.group(1)

    return None


# ============================================================
# PROCESS ONE JAVA FILE
# ============================================================

def process_java_file(
    java_file,
    problems
):

    print()
    print("=" * 60)
    print(
        f"Processing: {java_file}"
    )
    print("=" * 60)

    # --------------------------------------------------------
    # Get problem number
    # --------------------------------------------------------

    problem_number = extract_problem_number(
        java_file
    )

    if problem_number is None:

        print()
        print(
            "❌ Invalid filename."
        )

        print(
            "Filename must start with the "
            "LeetCode problem number."
        )

        print(
            "Example: 3090.java"
        )

        return False

    print()
    print(
        f"🔍 Problem detected: #{problem_number}"
    )

    # --------------------------------------------------------
    # Duplicate check
    # --------------------------------------------------------

    for existing in problems:

        if str(
            existing.get("number")
        ) == str(problem_number):

            print()
            print(
                "⚠️ This problem is already "
                "in the repository."
            )

            print(
                f"   {existing.get('number')} - "
                f"{existing.get('name')}"
            )

            return False

    # --------------------------------------------------------
    # Get LeetCode metadata
    # --------------------------------------------------------

    print()
    print(
        "🌐 Getting information from LeetCode..."
    )

    problem = get_leetcode_problem(
        problem_number
    )

    if problem is None:

        print()
        print(
            "❌ Could not get problem information."
        )

        return False

    # --------------------------------------------------------
    # Extract metadata
    # --------------------------------------------------------

    title = problem.get(
        "title",
        "Unknown"
    )

    difficulty = problem.get(
        "difficulty",
        "Unknown"
    )

    topics = [
        topic.get("name")
        for topic in problem.get(
            "topicTags",
            []
        )
    ]

    title_slug = problem.get(
        "titleSlug",
        ""
    )

    # --------------------------------------------------------
    # Display metadata
    # --------------------------------------------------------

    print()
    print("✅ Problem found!")

    print(
        f"   Number     : {problem_number}"
    )

    print(
        f"   Title      : {title}"
    )

    print(
        f"   Difficulty : {difficulty}"
    )

    print(
        f"   Topics     : "
        f"{', '.join(topics) if topics else 'None'}"
    )

    # --------------------------------------------------------
    # Create destination folder
    # --------------------------------------------------------

    difficulty_folder = difficulty.lower()

    if difficulty_folder not in [
        "easy",
        "medium",
        "hard"
    ]:

        difficulty_folder = "other"

    destination_folder = os.path.join(
        SOLUTIONS_FOLDER,
        difficulty_folder
    )

    os.makedirs(
        destination_folder,
        exist_ok=True
    )

    # --------------------------------------------------------
    # Create destination filename
    # --------------------------------------------------------

    safe_title = create_safe_filename(
        title
    )

    destination_filename = (
        f"{problem_number}-"
        f"{safe_title}.java"
    )

    destination_path = os.path.join(
        destination_folder,
        destination_filename
    )

    source_path = os.path.join(
        INCOMING_FOLDER,
        java_file
    )

    # --------------------------------------------------------
    # Check destination
    # --------------------------------------------------------

    if os.path.exists(
        destination_path
    ):

        print()
        print(
            "⚠️ Destination file already exists:"
        )

        print(
            f"   {destination_path}"
        )

        return False

    # --------------------------------------------------------
    # Move Java solution
    # --------------------------------------------------------

    try:

        shutil.move(
            source_path,
            destination_path
        )

    except Exception as e:

        print()
        print(
            "❌ Failed to move Java solution."
        )

        print(e)

        return False

    print()
    print(
        "📁 Solution organized:"
    )

    print(
        f"   {destination_path}"
    )

    # --------------------------------------------------------
    # Save metadata
    # --------------------------------------------------------

    relative_path = destination_path.replace(
        os.sep,
        "/"
    )

    problem_data = {

        "number": problem_number,

        "name": title,

        "slug": title_slug,

        "difficulty": difficulty,

        "topics": topics,

        "language": "Java",

        "file_path": relative_path

    }

    problems.append(
        problem_data
    )

    save_problems(
        problems
    )

    print()
    print(
        "💾 problems.json updated."
    )

    return True


# ============================================================
# MAIN
# ============================================================

def main():

    print()
    print("=" * 60)
    print(
        "             🚀 LEETCODE DAILY AUTOMATOR"
    )
    print("=" * 60)
    print()

    # --------------------------------------------------------
    # Create folders if needed
    # --------------------------------------------------------

    os.makedirs(
        INCOMING_FOLDER,
        exist_ok=True
    )

    os.makedirs(
        SOLUTIONS_FOLDER,
        exist_ok=True
    )

    os.makedirs(
        "data",
        exist_ok=True
    )

    # --------------------------------------------------------
    # Find Java files
    # --------------------------------------------------------

    java_files = [

        file

        for file in os.listdir(
            INCOMING_FOLDER
        )

        if file.lower().endswith(".java")

    ]

    if not java_files:

        print(
            "ℹ️ No new Java solutions found."
        )

        print()
        print(
            "Put your Java solution inside:"
        )

        print(
            "incoming/"
        )

        return

    print(
        f"📦 Found {len(java_files)} "
        f"Java solution(s)."
    )

    # --------------------------------------------------------
    # Load database
    # --------------------------------------------------------

    problems = load_problems()

    successful = 0

    # --------------------------------------------------------
    # Process files
    # --------------------------------------------------------

    for java_file in java_files:

        if process_java_file(
            java_file,
            problems
        ):

            successful += 1

    # --------------------------------------------------------
    # Result
    # --------------------------------------------------------

    print()
    print("=" * 60)
    print(
        "                    RESULT"
    )
    print("=" * 60)

    print()

    print(
        f"✅ Successfully processed: "
        f"{successful}"
    )

    print(
        f"📊 Total problems stored: "
        f"{len(problems)}"
    )

    print()


# ============================================================
# START
# ============================================================

if __name__ == "__main__":
    main()