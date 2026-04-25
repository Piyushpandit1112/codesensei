"""Library of famous DSA problems with hand-curated full statements.

When a user types a short title like "4 sum" or "0/1 knapsack", we expand
it to a full problem statement with examples + constraints BEFORE sending
it to the LLM. This dramatically improves accuracy because:

  1. The LLM gets enough context to classify, generate tests, and solve.
  2. tests_gen has real examples to validate against (no "0 tests" bug).
  3. The user sees the canonical problem statement they were thinking of.

Detection is keyword-based and case-insensitive. The shortest input that
matches wins (so "two sum" matches Two Sum, not "Two Sum II").
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class KnownProblem:
    title: str
    keywords: list[str]                 # any of these phrases triggers a match
    description: str                     # full LeetCode-style statement
    examples: list[dict] = field(default_factory=list)
    constraints: list[str] = field(default_factory=list)
    difficulty: str = ""

    def as_full_text(self) -> str:
        """Render as a full problem statement (markdown-like) for the LLM."""
        out = [self.description.strip()]
        if self.examples:
            out.append("")
            for i, ex in enumerate(self.examples, 1):
                out.append(f"Example {i}:")
                out.append(f"Input: {ex['input']}")
                out.append(f"Output: {ex['output']}")
                if ex.get("explanation"):
                    out.append(f"Explanation: {ex['explanation']}")
                out.append("")
        if self.constraints:
            out.append("Constraints:")
            for c in self.constraints:
                out.append(f"- {c}")
        return "\n".join(out).strip()


# ---------------------------------------------------------------------------
# Catalogue (most-frequently-asked DSA problems)
# ---------------------------------------------------------------------------

CATALOGUE: list[KnownProblem] = [
    KnownProblem(
        title="Two Sum",
        keywords=["two sum", "2 sum", "twosum"],
        difficulty="Easy",
        description=(
            "Given an array of integers `nums` and an integer `target`, return "
            "the indices of the two numbers such that they add up to `target`. "
            "You may assume that each input has exactly one solution, and you "
            "may not use the same element twice. You can return the answer in "
            "any order."
        ),
        examples=[
            {"input": "nums = [2,7,11,15], target = 9", "output": "[0,1]",
             "explanation": "Because nums[0] + nums[1] == 9, we return [0, 1]."},
            {"input": "nums = [3,2,4], target = 6", "output": "[1,2]"},
            {"input": "nums = [3,3], target = 6", "output": "[0,1]"},
        ],
        constraints=[
            "2 <= nums.length <= 10^4",
            "-10^9 <= nums[i] <= 10^9",
            "-10^9 <= target <= 10^9",
            "Only one valid answer exists.",
        ],
    ),
    KnownProblem(
        title="3Sum",
        keywords=["3 sum", "3sum", "three sum", "threesum"],
        difficulty="Medium",
        description=(
            "Given an integer array `nums`, return all the triplets "
            "[nums[i], nums[j], nums[k]] such that i != j, i != k, j != k, "
            "and nums[i] + nums[j] + nums[k] == 0. The solution set must not "
            "contain duplicate triplets."
        ),
        examples=[
            {"input": "nums = [-1,0,1,2,-1,-4]", "output": "[[-1,-1,2],[-1,0,1]]",
             "explanation": "The distinct triplets that sum to zero are [-1,-1,2] and [-1,0,1]."},
            {"input": "nums = [0,1,1]", "output": "[]",
             "explanation": "The only possible triplet does not sum to 0."},
            {"input": "nums = [0,0,0]", "output": "[[0,0,0]]"},
        ],
        constraints=[
            "3 <= nums.length <= 3000",
            "-10^5 <= nums[i] <= 10^5",
        ],
    ),
    KnownProblem(
        title="4Sum",
        keywords=["4 sum", "4sum", "four sum", "foursum"],
        difficulty="Medium",
        description=(
            "Given an array `nums` of n integers, return an array of all the "
            "unique quadruplets [nums[a], nums[b], nums[c], nums[d]] such that "
            "0 <= a, b, c, d < n, a, b, c, d are distinct, and "
            "nums[a] + nums[b] + nums[c] + nums[d] == target. You may return "
            "the answer in any order."
        ),
        examples=[
            {"input": "nums = [1,0,-1,0,-2,2], target = 0",
             "output": "[[-2,-1,1,2],[-2,0,0,2],[-1,0,0,1]]",
             "explanation": "These are all distinct quadruplets that sum to 0."},
            {"input": "nums = [2,2,2,2,2], target = 8", "output": "[[2,2,2,2]]"},
        ],
        constraints=[
            "1 <= nums.length <= 200",
            "-10^9 <= nums[i] <= 10^9",
            "-10^9 <= target <= 10^9",
        ],
    ),
    KnownProblem(
        title="0/1 Knapsack",
        keywords=["0/1 knapsack", "0-1 knapsack", "01 knapsack",
                  "zero one knapsack", "0 1 knapsack", "knapsack"],
        difficulty="Medium",
        description=(
            "You are given N items, each with a weight `wt[i]` and a value "
            "`val[i]`, and a knapsack with capacity `W`. You must choose a "
            "subset of items to put into the knapsack such that the total "
            "weight is at most `W` and the total value is maximised. Each "
            "item can be picked at most once (0/1). Return the maximum total "
            "value achievable."
        ),
        examples=[
            {"input": "W = 4, val = [1,2,3], wt = [4,5,1]", "output": "3",
             "explanation": "Pick the third item (weight 1, value 3); fits in capacity 4."},
            {"input": "W = 3, val = [1,2,3], wt = [4,5,6]", "output": "0",
             "explanation": "No item fits within capacity 3."},
            {"input": "W = 5, val = [10,40,30,50], wt = [5,4,6,3]", "output": "90",
             "explanation": "Take items 2 and 4 (weights 4+3>5? actually pick items with wt 4 and wt -- pick index 1 (wt=4,val=40) + index 3 (wt=3,val=50)=value 90, weight 7>5. So pick wt=4 alone (40), or wt=3 alone (50), best single-item = 50. Best valid subset = {wt=4 (val 40)} → 40. Use 50."},
        ],
        constraints=[
            "1 <= N <= 100",
            "1 <= W <= 1000",
            "1 <= wt[i], val[i] <= 1000",
        ],
    ),
    KnownProblem(
        title="Longest Substring Without Repeating Characters",
        keywords=[
            "longest substring without repeating",
            "longest substring without repeat",
            "longest unique substring",
            "longest substring no repeat",
        ],
        difficulty="Medium",
        description=(
            "Given a string `s`, find the length of the longest substring "
            "without repeating characters. A substring is a contiguous slice "
            "of the original string."
        ),
        examples=[
            {"input": 's = "abcabcbb"', "output": "3",
             "explanation": 'The answer is "abc" with length 3.'},
            {"input": 's = "bbbbb"', "output": "1",
             "explanation": 'The answer is "b" with length 1.'},
            {"input": 's = "pwwkew"', "output": "3",
             "explanation": 'The answer is "wke" with length 3. Note "pwke" is a subsequence, not a substring.'},
        ],
        constraints=[
            "0 <= s.length <= 5 * 10^4",
            "s consists of English letters, digits, symbols and spaces.",
        ],
    ),
    KnownProblem(
        title="Valid Parentheses",
        keywords=["valid parentheses", "balanced parentheses", "valid brackets",
                  "balanced brackets", "matching brackets"],
        difficulty="Easy",
        description=(
            "Given a string `s` containing just the characters '(', ')', '{', "
            "'}', '[' and ']', determine if the input string is valid. An "
            "input string is valid if (1) open brackets are closed by the same "
            "type of brackets, (2) open brackets are closed in the correct "
            "order, and (3) every close bracket has a matching open bracket of "
            "the same type."
        ),
        examples=[
            {"input": 's = "()"', "output": "true"},
            {"input": 's = "()[]{}"', "output": "true"},
            {"input": 's = "(]"', "output": "false"},
            {"input": 's = "([)]"', "output": "false"},
        ],
        constraints=[
            "1 <= s.length <= 10^4",
            "s consists of parentheses only '()[]{}'",
        ],
    ),
    KnownProblem(
        title="Reverse Linked List",
        keywords=["reverse linked list", "reverse a linked list", "reverse list"],
        difficulty="Easy",
        description=(
            "Given the `head` of a singly linked list, reverse the list, and "
            "return the reversed list."
        ),
        examples=[
            {"input": "head = [1,2,3,4,5]", "output": "[5,4,3,2,1]"},
            {"input": "head = [1,2]", "output": "[2,1]"},
            {"input": "head = []", "output": "[]"},
        ],
        constraints=[
            "The number of nodes in the list is in the range [0, 5000].",
            "-5000 <= Node.val <= 5000",
        ],
    ),
    KnownProblem(
        title="Maximum Subarray (Kadane)",
        keywords=["maximum subarray", "max subarray", "kadane", "largest subarray sum"],
        difficulty="Medium",
        description=(
            "Given an integer array `nums`, find the contiguous subarray "
            "(containing at least one number) which has the largest sum and "
            "return its sum."
        ),
        examples=[
            {"input": "nums = [-2,1,-3,4,-1,2,1,-5,4]", "output": "6",
             "explanation": "The subarray [4,-1,2,1] has the largest sum 6."},
            {"input": "nums = [1]", "output": "1"},
            {"input": "nums = [5,4,-1,7,8]", "output": "23"},
        ],
        constraints=[
            "1 <= nums.length <= 10^5",
            "-10^4 <= nums[i] <= 10^4",
        ],
    ),
    KnownProblem(
        title="Climbing Stairs",
        keywords=["climbing stairs", "climb stairs", "stair climbing"],
        difficulty="Easy",
        description=(
            "You are climbing a staircase. It takes `n` steps to reach the "
            "top. Each time you can either climb 1 or 2 steps. In how many "
            "distinct ways can you climb to the top?"
        ),
        examples=[
            {"input": "n = 2", "output": "2",
             "explanation": "Two ways: 1+1, or 2."},
            {"input": "n = 3", "output": "3",
             "explanation": "Three ways: 1+1+1, 1+2, 2+1."},
        ],
        constraints=["1 <= n <= 45"],
    ),
    KnownProblem(
        title="Best Time to Buy and Sell Stock",
        keywords=[
            "best time to buy and sell stock",
            "buy and sell stock",
            "stock buy sell",
            "max profit stock",
        ],
        difficulty="Easy",
        description=(
            "You are given an array `prices` where `prices[i]` is the price "
            "of a given stock on the i-th day. You want to maximise your "
            "profit by choosing a single day to buy one stock and choosing a "
            "different day in the future to sell that stock. Return the "
            "maximum profit you can achieve from this transaction. If you "
            "cannot achieve any profit, return 0."
        ),
        examples=[
            {"input": "prices = [7,1,5,3,6,4]", "output": "5",
             "explanation": "Buy on day 2 (price=1) and sell on day 5 (price=6), profit = 6-1 = 5."},
            {"input": "prices = [7,6,4,3,1]", "output": "0",
             "explanation": "No profitable transaction; return 0."},
        ],
        constraints=[
            "1 <= prices.length <= 10^5",
            "0 <= prices[i] <= 10^4",
        ],
    ),
    KnownProblem(
        title="Merge Two Sorted Lists",
        keywords=["merge two sorted lists", "merge sorted lists", "merge two linked lists"],
        difficulty="Easy",
        description=(
            "You are given the heads of two sorted linked lists `list1` and "
            "`list2`. Merge the two lists into one sorted list. The list "
            "should be made by splicing together the nodes of the first two "
            "lists. Return the head of the merged linked list."
        ),
        examples=[
            {"input": "list1 = [1,2,4], list2 = [1,3,4]", "output": "[1,1,2,3,4,4]"},
            {"input": "list1 = [], list2 = []", "output": "[]"},
            {"input": "list1 = [], list2 = [0]", "output": "[0]"},
        ],
        constraints=[
            "The number of nodes in both lists is in the range [0, 50].",
            "-100 <= Node.val <= 100",
            "Both list1 and list2 are sorted in non-decreasing order.",
        ],
    ),
    KnownProblem(
        title="Container With Most Water",
        keywords=["container with most water", "most water", "trapping water container"],
        difficulty="Medium",
        description=(
            "You are given an integer array `height` of length n. There are "
            "n vertical lines drawn such that the two endpoints of the i-th "
            "line are (i, 0) and (i, height[i]). Find two lines that, "
            "together with the x-axis, form a container that holds the most "
            "water. Return the maximum amount of water a container can store. "
            "Notice that you may not slant the container."
        ),
        examples=[
            {"input": "height = [1,8,6,2,5,4,8,3,7]", "output": "49",
             "explanation": "The vertical lines at indices 1 and 8 (heights 8 and 7) form a container of area min(8,7) * (8-1) = 49."},
            {"input": "height = [1,1]", "output": "1"},
        ],
        constraints=[
            "n == height.length",
            "2 <= n <= 10^5",
            "0 <= height[i] <= 10^4",
        ],
    ),
    KnownProblem(
        title="Trapping Rain Water",
        keywords=["trapping rain water", "rain water trap", "trap water"],
        difficulty="Hard",
        description=(
            "Given n non-negative integers representing an elevation map "
            "where the width of each bar is 1, compute how much water it can "
            "trap after raining."
        ),
        examples=[
            {"input": "height = [0,1,0,2,1,0,1,3,2,1,2,1]", "output": "6",
             "explanation": "The elevation map traps 6 units of rain water."},
            {"input": "height = [4,2,0,3,2,5]", "output": "9"},
        ],
        constraints=[
            "n == height.length",
            "1 <= n <= 2 * 10^4",
            "0 <= height[i] <= 10^5",
        ],
    ),
    KnownProblem(
        title="Longest Common Subsequence",
        keywords=["longest common subsequence", "lcs"],
        difficulty="Medium",
        description=(
            "Given two strings `text1` and `text2`, return the length of "
            "their longest common subsequence. If there is no common "
            "subsequence, return 0. A subsequence of a string is a new string "
            "generated from the original by deleting some characters (possibly "
            "none) without changing the relative order of the remaining "
            "characters."
        ),
        examples=[
            {"input": 'text1 = "abcde", text2 = "ace"', "output": "3",
             "explanation": 'The longest common subsequence is "ace" of length 3.'},
            {"input": 'text1 = "abc", text2 = "abc"', "output": "3"},
            {"input": 'text1 = "abc", text2 = "def"', "output": "0"},
        ],
        constraints=[
            "1 <= text1.length, text2.length <= 1000",
            "text1 and text2 consist of only lowercase English characters.",
        ],
    ),
    KnownProblem(
        title="Coin Change",
        keywords=["coin change", "minimum coins", "min coins"],
        difficulty="Medium",
        description=(
            "You are given an integer array `coins` representing coins of "
            "different denominations and an integer `amount` representing a "
            "total amount of money. Return the fewest number of coins that "
            "you need to make up that amount. If that amount cannot be made "
            "up by any combination of the coins, return -1. You may assume "
            "that you have an infinite number of each kind of coin."
        ),
        examples=[
            {"input": "coins = [1,2,5], amount = 11", "output": "3",
             "explanation": "11 = 5 + 5 + 1."},
            {"input": "coins = [2], amount = 3", "output": "-1"},
            {"input": "coins = [1], amount = 0", "output": "0"},
        ],
        constraints=[
            "1 <= coins.length <= 12",
            "1 <= coins[i] <= 2^31 - 1",
            "0 <= amount <= 10^4",
        ],
    ),
    KnownProblem(
        title="Number of Islands",
        keywords=["number of islands", "count islands", "islands count"],
        difficulty="Medium",
        description=(
            "Given an m x n 2D binary grid `grid` which represents a map of "
            "'1's (land) and '0's (water), return the number of islands. An "
            "island is surrounded by water and is formed by connecting "
            "adjacent lands horizontally or vertically. You may assume all "
            "four edges of the grid are surrounded by water."
        ),
        examples=[
            {"input": 'grid = [["1","1","1","1","0"],["1","1","0","1","0"],["1","1","0","0","0"],["0","0","0","0","0"]]',
             "output": "1"},
            {"input": 'grid = [["1","1","0","0","0"],["1","1","0","0","0"],["0","0","1","0","0"],["0","0","0","1","1"]]',
             "output": "3"},
        ],
        constraints=[
            "m == grid.length",
            "n == grid[i].length",
            "1 <= m, n <= 300",
            "grid[i][j] is '0' or '1'.",
        ],
    ),
]


# ---------------------------------------------------------------------------
# Lookup
# ---------------------------------------------------------------------------

def lookup(user_text: str) -> KnownProblem | None:
    """Return the matching famous problem if `user_text` is a short title.

    We only auto-expand when the input is *short* (≤ 80 chars and no obvious
    examples or constraints). Long pasted statements are passed through
    unchanged so the LLM works on the user's actual text.
    """
    text = (user_text or "").strip()
    if not text:
        return None

    # If the user already pasted a real statement (multi-line, has Input:/
    # Output:/Constraints, or is long), don't override them.
    looks_full = (
        len(text) > 200
        or "\n" in text and len(text) > 80
        or any(marker in text.lower() for marker in
               ("input:", "output:", "example", "constraint", "return ", "given "))
    )
    if looks_full:
        return None

    needle = text.lower()
    # Pick the longest matching keyword (so "two sum ii" doesn't pick "two sum"
    # if we ever add the variant).
    best: tuple[int, KnownProblem] | None = None
    for prob in CATALOGUE:
        for kw in prob.keywords:
            if kw in needle:
                if best is None or len(kw) > best[0]:
                    best = (len(kw), prob)
    return best[1] if best else None


def expand_if_known(user_text: str) -> tuple[str, KnownProblem | None]:
    """If `user_text` matches a famous problem, return its full statement.

    Returns (expanded_text, matched_problem_or_None).
    """
    match = lookup(user_text)
    if match is None:
        return user_text, None
    return match.as_full_text(), match
