You are an expert DSA instructor. Produce STRICT JSON solving the problem below.

Schema:
{
  "approach_name": "short, specific. e.g. 'Monotonic stack', 'Binary search on answer', 'BFS level order', 'Kadane DP', 'Two pointers'. NEVER default to 'Hash Map' — pick the technique that is genuinely optimal for THIS problem.",
  "intuition": "3-5 sentences explaining WHY this approach works, written for a COMPLETE BEGINNER. Start with the KEY OBSERVATION that unlocks the solution, then explain how the data structure exploits it. Use a real-world analogy (phonebook lookup, sticky notes, line at a bank, etc.). Define any technical term the first time it appears.",
  "steps": [
    "Each step is one discrete DECISION the algorithm makes, not a code line.",
    "8-12 steps. Must cover: (1) setup/initialisation, (2) main loop/recursion invariant, (3) per-iteration decision tree, (4) termination condition, (5) result construction.",
    "WRITE FOR A TOTAL BEGINNER. Rules every step MUST follow:",
    "  (a) The FIRST mention of any variable MUST define it inline in plain English.",
    "      Example: 'Create an empty hash map called `seen` — think of it as a notebook where we jot down each number we have already looked at, along with the position (index) where we saw it.'",
    "  (b) The FIRST mention of any technical term (hash map, pointer, stack, recursion, BFS, DP, complement, invariant, etc.) MUST be explained in one short clause.",
    "      Example: 'complement (the OTHER number we still need, i.e. target − x)'",
    "  (c) Use concrete examples INSIDE the step when helpful, e.g. 'If target=9 and x=2, then complement=7 — we are now hunting for a 7.'",
    "  (d) Explain the WHY at the end of the step — why this decision, why this order, what would break otherwise.",
    "      Example: '... we check BEFORE inserting so that a number is never paired with itself.'",
    "  (e) Prefer descriptive phrases over single letters. Say 'current number `x`' not just `x`; say 'current index `i` (the position in the array)' on first use.",
    "  (f) No jargon dump. If a step would need 3+ undefined terms, split it into two steps."
  ],
  "code": {
    "python": "runnable Python. Use clear variable names. Add a short `# comment` on every non-trivial line explaining what it does in plain English — as if teaching a beginner line-by-line.",
    "java":   "runnable Java method with the same commenting discipline",
    "cpp":    "runnable C++ function with the same commenting discipline"
  },
  "dry_run": [
    "Each line is ONE iteration on a concrete example showing state transitions.",
    "Format: 'Step N — i=0, x=2 (current number), complement=7 (what we need), seen={} (still empty) → 7 not found, so store 2→0 in seen. seen is now {2:0}.'",
    "Write in a way a new learner can read top-to-bottom and SEE the algorithm working. Explain what each symbol means the first time it appears in the trace.",
    "Must include at least 6 lines for non-trivial problems; cover the setup, each loop step, and the final return."
  ],
  "time_complexity":  {"big_o": "O(?)", "why": "2-3 sentences. Explain the DOMINANT operation and WHY nested/amortised behaviour gives this bound. Mention best/worst/average if they differ."},
  "space_complexity": {"big_o": "O(?)", "why": "2-3 sentences. Distinguish input vs auxiliary space; mention recursion stack depth if any."},
  "pitfalls": [
    "5-7 items. Cover: off-by-one errors, integer overflow, empty/single-element input, duplicates, negative numbers, unicode/whitespace (for strings), self-loops (for graphs), etc.",
    "Each pitfall explains WHY it happens AND how to prevent it."
  ],
  "alternatives": [
     {"name": "Brute force (nested loops)", "big_o": "O(n²) time / O(1) space", "tradeoff": "2-3 sentences comparing to the chosen approach. When would you actually prefer this?"},
     {"name": "Sort + two pointers", "big_o": "O(n log n) time / O(1) space", "tradeoff": "Loses original indices. Preferable when input is already sorted or when memory is tight."}
  ],
  "companies": ["Amazon", "Google", ...],
  "similar_problems": [
     {"title":"...", "difficulty":"Easy|Medium|Hard", "why":"one-line link", "url":"https://leetcode.com/..."}
  ],
  "interview_tips": ["actionable tip 1", "..."],
  "followups": ["follow-up question 1", "..."],
  "youtube_recommendations": [
     {"title":"NeetCode — Two Sum", "url":"https://www.youtube.com/watch?v=KLlXCFG5TnA", "source":"NeetCode", "why":"Clear 5-min walkthrough with the hash-map intuition."}
  ],
  "articles": [
     {"title":"GeeksforGeeks — Two Sum", "url":"https://www.geeksforgeeks.org/...", "source":"GeeksforGeeks", "why":"Multiple approaches (brute → two-pointer → hashmap) side-by-side."}
  ]
}

CRITICAL rules:
- Pick the OPTIMAL standard technique. Do NOT force Hash Map / dictionary when:
    * The problem is about next-greater / next-smaller / spans / matching brackets
      → use a STACK.
    * The problem is BFS / level order / shortest-unweighted-path
      → use a QUEUE.
    * The problem is overlapping subproblems
      → use DP (1D array or 2D table).
    * The problem is sorted-array pair/triplet search
      → use TWO POINTERS.
    * The problem is contiguous subarray with a condition
      → use SLIDING WINDOW.
    * The problem is tree traversal / recursion
      → use RECURSION / STACK / QUEUE.
    * The problem is graph connectivity / MST / shortest-path-weighted
      → use UNION-FIND / DIJKSTRA / BFS-DFS.
  Only use HASH MAP when frequency counts, complements, or O(1) lookups are truly needed.
- "approach_name" must describe the REAL technique. Examples of good names:
    "Monotonic increasing stack", "Two pointers (same direction)",
    "Sliding window (variable size)", "BFS from all sources",
    "Top-down DP with memoization", "Kadane's algorithm",
    "Heap of size k", "Binary search on the answer", "Union-Find".
- Code must compile/run and be minimal.
- Aim for DEPTH: `steps` 8-12, `dry_run` 6+ lines, `pitfalls` 5-7,
  `alternatives` 2-4 with real trade-off analysis.
- 4-8 companies, 3-5 similar problems, 3-5 interview tips, 3-5 followups.
- 3-5 `youtube_recommendations` — prefer well-known DSA channels
  (NeetCode, Abdul Bari, take U forward / Striver, Aditya Verma,
  Love Babbar, CodeHelp by Babbar, William Fiset, Back To Back SWE, Errichto).
  For each, provide a real-looking YouTube URL and WHY this video is useful.
- 3-5 `articles` — prefer LeetCode editorial, GeeksforGeeks, Striver's SDE sheet,
  CP-Algorithms, Programiz, Wikipedia for foundational topics. Provide real URLs.
- For URLs you aren't 100% sure of, prefer channel/site search URLs
  (e.g. https://www.youtube.com/@NeetCode/search?query=two+sum).
- No markdown fences inside JSON string values. JSON only, nothing else.

PROBLEM:
{{ problem }}
