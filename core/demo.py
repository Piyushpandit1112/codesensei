"""Hardcoded Two Sum fixture so the app works without any API keys."""
from __future__ import annotations

from .schemas import (
    Alternative,
    CodeBundle,
    ComplexityNote,
    Example,
    Frame,
    FrameScript,
    ProblemMeta,
    Resource,
    SimilarProblem,
    Solution,
)

PROBLEM = (
    "Given an array of integers nums and an integer target, return indices of the "
    "two numbers such that they add up to target. You may assume exactly one "
    "solution exists, and you may not use the same element twice."
)

META = ProblemMeta(
    title="Two Sum",
    topic="Array / Hash Map",
    difficulty="Easy",
    template_hint="hashmap",
    description=(
        "Given an integer array nums and an integer target, return indices of the two "
        "numbers such that they add up to target. Exactly one solution exists, and the "
        "same element may not be used twice."
    ),
    examples=[
        Example(
            input="nums = [2,7,11,15], target = 9",
            output="[0, 1]",
            explanation="Because nums[0] + nums[1] == 9, we return [0, 1].",
        ),
        Example(
            input="nums = [3,2,4], target = 6",
            output="[1, 2]",
            explanation="nums[1] + nums[2] = 2 + 4 = 6.",
        ),
    ],
    constraints=[
        "2 <= nums.length <= 10^4",
        "-10^9 <= nums[i] <= 10^9",
        "-10^9 <= target <= 10^9",
        "Only one valid answer exists.",
    ],
)

SOLUTION = Solution(
    approach_name="Hash Map — one pass",
    intuition=(
        "Think of it like finding a matching sock in a drawer. For every number `x` "
        "we pick up, we are really asking: 'have I already seen its partner — the "
        "number `target − x` — earlier in the array?' A plain second loop would "
        "re-scan the array for every `x` (slow, O(n²)). Instead, we keep a small "
        "notebook called a HASH MAP — a data structure that stores key → value "
        "pairs and lets us check 'is this key inside?' in essentially one step "
        "(O(1)). So as we walk the array once, we ask the notebook before we "
        "write in it, and the first time the partner is already there, we are done."
    ),
    steps=[
        "Create an empty hash map called `seen`. A hash map is like a notebook of "
        "key→value pairs; here the KEY is a number from the array and the VALUE is "
        "the INDEX (position, 0-based) where we saw it. It starts empty: `seen = {}`.",

        "Walk through the array `nums` one element at a time. At each step we "
        "track two things: `i` = the current index (position), and `x` = the "
        "number sitting at that position, i.e. `x = nums[i]`.",

        "Compute the COMPLEMENT — the OTHER number we still need so that "
        "`x + complement == target`. So `complement = target − x`. "
        "Example: if `target = 9` and `x = 2`, then `complement = 7` — we are "
        "now hunting for a 7 somewhere earlier in the array.",

        "Look up `complement` inside `seen`. Because `seen` is a hash map, this "
        "lookup takes constant time — it does NOT re-scan the array. "
        "We check BEFORE inserting the current number, so a number can never be "
        "paired with itself (the problem forbids that).",

        "If `complement` IS already in `seen`, we have found the pair. "
        "`seen[complement]` gives us the earlier index where the partner was "
        "stored; combined with the current index `i`, we return "
        "`[seen[complement], i]` and stop.",

        "If `complement` is NOT in `seen`, this current `x` might still be the "
        "partner for some FUTURE element. So we record it by writing "
        "`seen[x] = i` — meaning 'number `x` was last seen at index `i`'.",

        "Move to the next index and repeat. The problem guarantees exactly one "
        "valid pair exists, so the loop is certain to return before it finishes.",
    ],
    code=CodeBundle(
        python=(
            "def twoSum(nums, target):\n"
            "    seen = {}                         # notebook: number -> index\n"
            "    for i, x in enumerate(nums):      # i = position, x = value at that position\n"
            "        c = target - x                # c = complement, the partner we still need\n"
            "        if c in seen:                 # have we already recorded that partner?\n"
            "            return [seen[c], i]       # yes -> return [earlier index, current index]\n"
            "        seen[x] = i                   # no  -> remember x for future lookups\n"
        ),
        java=(
            "public int[] twoSum(int[] nums, int target) {\n"
            "    // seen maps a number -> the index where we last saw it\n"
            "    Map<Integer,Integer> seen = new HashMap<>();\n"
            "    for (int i = 0; i < nums.length; i++) {\n"
            "        int c = target - nums[i];                  // complement we need\n"
            "        if (seen.containsKey(c))                    // partner already seen?\n"
            "            return new int[]{seen.get(c), i};       // yes -> return both indices\n"
            "        seen.put(nums[i], i);                       // no  -> remember this one\n"
            "    }\n"
            "    return new int[]{};\n"
            "}\n"
        ),
        cpp=(
            "vector<int> twoSum(vector<int>& nums, int target) {\n"
            "    unordered_map<int,int> seen;                 // number -> index\n"
            "    for (int i = 0; i < (int)nums.size(); ++i) {\n"
            "        int c = target - nums[i];                // complement\n"
            "        if (seen.count(c)) return {seen[c], i};  // found the pair\n"
            "        seen[nums[i]] = i;                       // otherwise remember it\n"
            "    }\n"
            "    return {};\n"
            "}\n"
        ),
    ),
    dry_run=[
        "Setup — nums = [2, 7, 11, 15], target = 9, seen = {} (empty notebook).",
        "Step 1 — i=0, x=2 (current number). complement = 9 − 2 = 7 (what we need). "
        "Is 7 inside seen? seen is {} → NO. So we write 2→0 into the notebook. "
        "seen is now {2: 0}.",
        "Step 2 — i=1, x=7 (current number). complement = 9 − 7 = 2 (what we need). "
        "Is 2 inside seen? YES — seen[2] = 0. "
        "We return [seen[2], i] = [0, 1]. Done.",
        "(Indices 2 and 3 are never visited because the answer was already found.)",
    ],
    time_complexity=ComplexityNote(
        big_o="O(n)",
        why=(
            "We traverse the array exactly once — that is n steps. Inside each "
            "step we do a hash-map lookup and (maybe) an insert, both of which "
            "take amortised O(1) time. So the total work grows linearly with the "
            "input size."
        ),
    ),
    space_complexity=ComplexityNote(
        big_o="O(n)",
        why=(
            "In the worst case (the matching pair is the last element) we may "
            "have stored all the earlier n−1 numbers in `seen` before finding "
            "the answer. So the auxiliary memory scales with n. The input array "
            "itself is not counted."
        ),
    ),
    pitfalls=[
        "Using the same element twice — if you insert `x` into `seen` BEFORE "
        "checking for its complement, an input like nums=[3,3], target=6 could "
        "incorrectly match index 0 with itself. Always check first, insert after.",
        "Returning VALUES instead of INDICES — the problem asks for positions "
        "`[i, j]`, not the numbers themselves.",
        "Assuming the array is sorted — it is NOT. Two-pointer tricks that "
        "require sorting will change the original indices and break the answer.",
        "Integer overflow in other languages — `target − x` can exceed 32-bit "
        "range when both are near ±10⁹. Use `long` in Java/C++ if needed.",
        "Empty / single-element arrays — the constraints say n ≥ 2, but always "
        "confirm with the interviewer. The loop handles n ≥ 2 naturally.",
    ],
    alternatives=[
        Alternative(
            name="Brute force",
            big_o="O(n^2) time / O(1) space",
            tradeoff="Simple but slow for large n.",
        ),
        Alternative(
            name="Sort + two pointers",
            big_o="O(n log n) time / O(n) space",
            tradeoff="Loses original indices; must keep original positions.",
        ),
    ],
    companies=[
        "Amazon", "Google", "Microsoft", "Apple", "Facebook",
        "Adobe", "Bloomberg", "Uber",
    ],
    similar_problems=[
        SimilarProblem(
            title="3Sum",
            difficulty="Medium",
            why="Extends the two-sum hash/two-pointer idea to triplets.",
            url="https://leetcode.com/problems/3sum/",
        ),
        SimilarProblem(
            title="Two Sum II — Sorted Array",
            difficulty="Medium",
            why="Same problem when input is sorted → use two pointers, O(1) space.",
            url="https://leetcode.com/problems/two-sum-ii-input-array-is-sorted/",
        ),
        SimilarProblem(
            title="4Sum",
            difficulty="Medium",
            why="Nested two-sum; same complement idea, more loops.",
            url="https://leetcode.com/problems/4sum/",
        ),
        SimilarProblem(
            title="Subarray Sum Equals K",
            difficulty="Medium",
            why="Hash map of prefix sums — same 'remember what you've seen' trick.",
            url="https://leetcode.com/problems/subarray-sum-equals-k/",
        ),
    ],
    interview_tips=[
        "Start with brute force O(n^2), then motivate why hash lookup helps — shows trade-off awareness.",
        "Clarify assumptions first: duplicates? negatives? exactly-one vs any valid pair?",
        "Explain why you check the complement BEFORE inserting (avoids using the same index twice).",
        "State complexity explicitly: amortized O(1) lookups → O(n) total time.",
        "Mention trade-off: sorting + two pointers gives O(1) space but O(n log n) time.",
    ],
    followups=[
        "What if the array is sorted? (two-pointer, O(1) space)",
        "What if duplicates can form multiple valid pairs — return ALL of them?",
        "How would you scale this if nums has 10 billion elements? (streaming / chunking)",
        "Can you solve it without a hash map? Discuss trade-offs.",
        "What if the array is too large to fit in memory? (external sort + two pointers)",
    ],
    youtube_recommendations=[
        Resource(
            title="NeetCode — Two Sum",
            url="https://www.youtube.com/watch?v=KLlXCFG5TnA",
            source="NeetCode",
            why="5-min walkthrough from brute force to the hash-map insight.",
        ),
        Resource(
            title="take U forward — Two Sum (Striver)",
            url="https://www.youtube.com/results?search_query=striver+two+sum",
            source="take U forward",
            why="Covers brute, better (sort+two-pointer), and optimal hash-map — interview-style.",
        ),
        Resource(
            title="Abdul Bari — Hashing basics",
            url="https://www.youtube.com/results?search_query=abdul+bari+hashing",
            source="Abdul Bari",
            why="Deep dive on how hash maps achieve amortized O(1) lookups.",
        ),
    ],
    articles=[
        Resource(
            title="LeetCode Editorial — Two Sum",
            url="https://leetcode.com/problems/two-sum/editorial/",
            source="LeetCode",
            why="Official three approaches with complexity analysis.",
        ),
        Resource(
            title="GeeksforGeeks — Two Sum (find pair with given sum)",
            url="https://www.geeksforgeeks.org/given-an-array-a-and-a-number-x-check-for-pair-in-a-with-sum-as-x/",
            source="GeeksforGeeks",
            why="Compares 4 approaches side-by-side including the complement trick.",
        ),
        Resource(
            title="Striver SDE Sheet — Two Sum",
            url="https://takeuforward.org/data-structure/two-sum-check-if-a-pair-with-given-sum-exists-in-array/",
            source="takeuforward.org",
            why="Interview-grade write-up with clarifying questions you should ask.",
        ),
    ],
)


def _f(i, patch, hi, en, hl=None, ptr=None) -> Frame:
    return Frame(
        id=i,
        state_patch=patch,
        highlights=hl or [],
        pointers=ptr or {},
        annotation_en=en,
        annotation_hi=hi,
        duration_ms=2200,
    )


# --------------------------------------------------------------------------- #
# Curated test suite — visible 3, hidden ~30 (LeetCode style)
# --------------------------------------------------------------------------- #
def _tc(label: str, nums: list[int], target: int, expected: list[int], hidden: bool = True) -> dict:
    return {
        "input_label": f"nums = {nums}, target = {target}",
        "args": {"nums": nums, "target": target},
        "expected": expected,
        "label": label,
        "hidden": hidden,
    }


TESTS: list[dict] = [
    # ---- visible (examples from the problem) ----
    _tc("example 1 — classic pair at start", [2, 7, 11, 15], 9, [0, 1], hidden=False),
    _tc("example 2 — pair in the middle",    [3, 2, 4],      6, [1, 2], hidden=False),
    _tc("example 3 — pair with duplicates",  [3, 3],         6, [0, 1], hidden=False),

    # ---- hidden — small & typical ----
    _tc("two-element exact match",           [8, 1],        9, [0, 1]),
    _tc("two-element negatives",             [-4, 2],      -2, [0, 1]),
    _tc("three elements, first+last",        [4, 1, 5],     9, [0, 2]),
    _tc("five elements, middle+end",         [1, 5, 8, 10, 12], 22, [3, 4]),
    _tc("six elements, last two",            [1, 2, 4, 8, 16, 32], 48, [4, 5]),
    _tc("seven elements, first+one",         [100, 1, 2, 4, 8, 16, 32], 132, [0, 6]),

    # ---- hidden — duplicates & zeros ----
    _tc("duplicates valid pair",             [3, 3, 4, 7], 6, [0, 1]),
    _tc("zero plus number",                  [0, 4, 3, 0], 0, [0, 3]),
    _tc("zero target with pos+neg",          [-3, 4, 3, 90], 0, [0, 2]),
    _tc("explicit zero finder",              [0, 5, 11, 0, 7], 0, [0, 3]),

    # ---- hidden — negatives ----
    _tc("two negatives sum",                 [-1, -2, -3, -4, -5], -9, [3, 4]),
    _tc("negative target only one pair",     [5, 75, 25, -75], -50, [2, 3]),
    _tc("large negative target",             [-1000000000, -999999999, 1, 2], -1999999999, [0, 1]),

    # ---- hidden — extremes ----
    _tc("max positives near 1e9",            [1000000000, 999999999, 1, 2], 1999999999, [0, 1]),
    _tc("huge + tiny",                       [2147483646, 1],  2147483647, [0, 1]),
    _tc("two extremes opposite sign",        [-1000000000, 1000000000], 0, [0, 1]),

    # ---- hidden — position variety ----
    _tc("answer is first-two",               [4, 5, 8, 100, 12], 9, [0, 1]),
    _tc("answer is last-two",                [10, 22, 30, 40, 50], 90, [3, 4]),
    _tc("answer is first & last",            [3, 1, 2, 4, 8], 11, [0, 4]),

    # ---- hidden — powers-of-two (unique sums) ----
    _tc("powers-of-two mid-pair",            [1, 2, 4, 8, 16, 32, 64, 128], 24, [3, 4]),
    _tc("powers-of-two large pair",          [1, 2, 4, 8, 16, 32, 64, 128, 256, 512], 640, [7, 9]),
    _tc("odd-only arithmetic seq",           [1, 3, 5, 7, 9, 11, 13, 15, 17, 19], 36, [8, 9]),

    # ---- hidden — adversarial ----
    _tc("target = 2×value, one dup",         [5, 5, 10], 10, [0, 1]),
    _tc("would self-match if buggy",         [3, 2, 4], 6, [1, 2]),
    _tc("target equals dup-sum only",        [1, 2, 7, 3, 3], 6, [3, 4]),
    _tc("clutter before answer",             [10, 1, -1, 2, 7, 3], 10, [4, 5]),

    # ---- hidden — bigger ----
    _tc("n=20 last + first unique",          [100, 2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22, 24, 26, 28, 30, 32, 34, 36, 200], 300, [0, 19]),
    _tc("n=100 odd-only last two",           [i * 2 + 1 for i in range(100)], 396, [98, 99]),
]


FRAMES = FrameScript(
    template="hashmap",
    initial_state={
        "array": [2, 7, 11, 15],
        "hashmap": {},
        "vars": {"target": 9},
        "code": [
            "def two_sum(nums, target):",
            "    seen = {}",
            "    for i, x in enumerate(nums):",
            "        c = target - x",
            "        if c in seen:",
            "            return [seen[c], i]",
            "        seen[x] = i",
        ],
    },
    frames=[
        _f(0, {},
           "Dekho, humein is array me do aise numbers dhundhne hain jinka sum target nau banaye. "
           "Brute force me har pair check karna padta, jo n-square lagta — isliye ek smarter tareeka sochte hain.",
           "We need two numbers summing to 9. Brute force is n-squared, let's think smarter.",
           ptr={"line": 1}),
        _f(1, {},
           "Trick ye hai ki jaise hi koi number dikhe, uska complement yaani target minus current yaad rakh lo. "
           "Isi liye ek locker room jaisa hash map banate hain, jahan har dekha number apni index ke saath baithe.",
           "So we keep a hash map — like a locker room of seen numbers with their indices.",
           ptr={"line": 2}),
        _f(2, {},
           "Chalo pehle number pe aate hain — 2 mila. Iska saathi hona chahiye target minus 2, matlab 7. "
           "Sawaal ye — kya humne 7 kabhi dekha hai?",
           "First number is 2. Its partner must be 7. Have we seen 7 yet?",
           ptr={"i": 0, "line": 4}, hl=[0]),
        _f(3, {},
           "Locker abhi bilkul khaali hai, toh 7 dikhne ka sawaal hi nahi — "
           "lekin haar nahi maanenge, agla kadam uthate hain.",
           "The locker is empty, so 7 isn't there — but we're not done.",
           ptr={"i": 0, "line": 5}, hl=[0]),
        _f(4, {"hashmap": {"2": 0}},
           "Isliye current number 2 ko locker me daal dete hain, key 2 aur uski index zero ke saath. "
           "Is record ki wajah se aage koi 7 aaya, to jodi turant pehchani jaa sakegi.",
           "So we store 2 at index 0. This is what enables instant lookup later.",
           ptr={"i": 0, "line": 7}, hl=[0]),
        _f(5, {},
           "Ab aate hain agle number pe — 7 hai. Iska jodidaar chahiye target minus 7, yaani 2. "
           "Aur ye wahi 2 hai jo abhi locker me rakha gaya tha.",
           "Next is 7. Partner is 2 — which we just stored. Looks like a match.",
           ptr={"i": 1, "line": 4}, hl=[1]),
        _f(6, {},
           "Toh confirm ho gaya — 2 locker me hai index zero pe. "
           "Matlab current index one aur pehle wali index zero, yahi humara answer hai.",
           "Confirmed — 2 sits at index 0. That's our answer.",
           ptr={"i": 1, "line": 5}, hl=[0, 1]),
        _f(7, {"vars": {"answer": [0, 1]}},
           "Wah, mil gaya jawaab — indices zero aur one. "
           "Ek hi pass me hua, isiliye time linear hai; space bhi linear kyunki worst case me "
           "poore array ko locker me daalna pad sakta hai.",
           "Answer [0, 1]. One pass means O(n) time and O(n) space.",
           ptr={"line": 6}, hl=[0, 1]),
    ],
)
