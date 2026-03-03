"""
WebSocket Test Agent for EAZR Chat
60 prompts across 4 categories: Casual(10), General(10), Policy(20), Hard Multi-Q(20)

Usage:
    python ws_test_agent.py --all --token YOUR_JWT     # Run all 60 tests
    python ws_test_agent.py -i --token YOUR_JWT        # Interactive mode
    python ws_test_agent.py --test casual --token JWT  # Run specific category
    python ws_test_agent.py --url ws://host:port/ws/chat --token JWT
"""

import asyncio
import json
import time
import sys
import os
import ssl
import argparse
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    import websockets
except ImportError:
    print("\n  websockets not installed. Run: pip install websockets\n")
    sys.exit(1)


# ─── Colors ───────────────────────────────────────────────────────────────

class C:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"
    WHITE = "\033[97m"
    GRAY = "\033[90m"


def ts():
    return datetime.now().strftime("%H:%M:%S")


# ─── WebSocket Client ─────────────────────────────────────────────────────

class WSTestAgent:
    def __init__(self, url: str, token: str):
        self.url = url
        self.token = token
        self.ws = None
        self.connection_id = None
        self.user_id = None
        self.chat_session_id = None
        self.connected = False
        self.authenticated = False
        self._listener_task = None
        self._queue: asyncio.Queue = asyncio.Queue()
        # Results: list of dicts with prompt, answer, intent, action, category, pass/fail, reason
        self.results: List[Dict[str, Any]] = []

    async def connect(self) -> bool:
        try:
            ws_url = f"{self.url}?token={self.token}"
            print(f"  {C.GRAY}{ts()}{C.RESET}  {C.BLUE}Connecting to {self.url}...{C.RESET}")
            ssl_ctx = None
            if ws_url.startswith("wss://"):
                ssl_ctx = ssl.create_default_context()
                ssl_ctx.check_hostname = False
                ssl_ctx.verify_mode = ssl.CERT_NONE
            self.ws = await websockets.connect(ws_url, ping_interval=30, ping_timeout=10, max_size=2**20, ssl=ssl_ctx)
            self.connected = True
            self._listener_task = asyncio.create_task(self._listen())

            # Wait for auth
            msg = await self._wait_for("auth_success", timeout=15)
            if msg:
                self.authenticated = True
                self.connection_id = msg.get("connection_id")
                self.user_id = msg.get("user_id")
                self.chat_session_id = msg.get("chat_session_id")
                print(f"  {C.GRAY}{ts()}{C.RESET}  {C.GREEN}Authenticated: user_id={self.user_id}, session={self.chat_session_id}{C.RESET}")
                return True
            else:
                print(f"  {C.GRAY}{ts()}{C.RESET}  {C.RED}Auth timeout{C.RESET}")
                return False
        except Exception as e:
            print(f"  {C.GRAY}{ts()}{C.RESET}  {C.RED}Connection failed: {e}{C.RESET}")
            return False

    async def _listen(self):
        try:
            async for raw in self.ws:
                try:
                    await self._queue.put(json.loads(raw))
                except json.JSONDecodeError:
                    pass
        except websockets.ConnectionClosed:
            self.connected = False
        except Exception:
            self.connected = False

    async def _wait_for(self, msg_type: str, timeout: float = 15) -> Optional[Dict]:
        deadline = time.time() + timeout
        while time.time() < deadline:
            try:
                msg = await asyncio.wait_for(self._queue.get(), timeout=max(0.1, deadline - time.time()))
                if msg.get("type") == msg_type:
                    return msg
            except asyncio.TimeoutError:
                break
        return None

    async def _drain(self):
        """Drain all pending messages from the queue, including in-flight ones."""
        # First drain everything currently in the queue
        while not self._queue.empty():
            try:
                self._queue.get_nowait()
            except asyncio.QueueEmpty:
                break
        # Wait briefly for any in-flight messages from the server
        try:
            while True:
                await asyncio.wait_for(self._queue.get(), timeout=0.5)
        except asyncio.TimeoutError:
            pass

    async def reconnect(self) -> bool:
        """Reconnect if connection was lost."""
        print(f"  {C.GRAY}{ts()}{C.RESET}  {C.YELLOW}Reconnecting...{C.RESET}")
        if self._listener_task:
            self._listener_task.cancel()
        try:
            if self.ws:
                await self.ws.close()
        except Exception:
            pass

        self.connected = False
        self.authenticated = False
        self._queue = asyncio.Queue()
        return await self.connect()

    async def chat(self, query: str, timeout: float = 60) -> Dict[str, Any]:
        """Send chat and collect full response. Returns {response, intent, action, type, data}."""
        if not self.authenticated or not self.connected:
            if not await self.reconnect():
                return {"response": "[RECONNECT FAILED]", "intent": "", "action": "", "type": "error", "data": {}}

        await self._drain()

        try:
            await self.ws.send(json.dumps({
                "type": "chat",
                "chat_session_id": self.chat_session_id,
                "query": query
            }))
        except (websockets.ConnectionClosed, Exception) as e:
            # Connection lost — reconnect and retry once
            if await self.reconnect():
                try:
                    await self.ws.send(json.dumps({
                        "type": "chat",
                        "chat_session_id": self.chat_session_id,
                        "query": query
                    }))
                except Exception:
                    return {"response": f"[SEND FAILED: {e}]", "intent": "", "action": "", "type": "error", "data": {}}
            else:
                return {"response": f"[CONNECTION LOST: {e}]", "intent": "", "action": "", "type": "error", "data": {}}

        result = {"response": "", "intent": "", "action": "", "type": "timeout", "data": {}}
        deadline = time.time() + timeout
        stream_chunks = []

        while time.time() < deadline:
            try:
                msg = await asyncio.wait_for(self._queue.get(), timeout=min(deadline - time.time(), 20.0))
                mt = msg.get("type", "")

                if mt == "chat_message":
                    data = msg.get("data", msg) if isinstance(msg.get("data"), dict) else msg
                    result["response"] = data.get("response", "") or msg.get("response", "")
                    result["intent"] = msg.get("metadata", {}).get("intent", data.get("intent", ""))
                    result["action"] = data.get("action", "")
                    result["type"] = data.get("type", "chat_message")
                    result["data"] = data
                    break

                elif mt == "chat_stream":
                    stream_chunks.append(msg.get("chunk", ""))

                elif mt == "chat_stream_end":
                    data = msg.get("data", {}) if isinstance(msg.get("data"), dict) else {}
                    result["response"] = msg.get("full_response", "".join(stream_chunks))
                    result["intent"] = data.get("intent", "")
                    result["action"] = data.get("action", "")
                    result["type"] = data.get("type", "streamed")
                    result["data"] = data
                    break

                elif mt in ("thinking", "thinking_indicator", "pong", "unread_count",
                            "notification_settings", "dnd_status"):
                    continue

                elif mt in ("error", "auth_failure"):
                    result["response"] = msg.get("error", "Error")
                    result["type"] = "error"
                    break

            except asyncio.TimeoutError:
                if stream_chunks:
                    continue
                break

        if not result["response"]:
            result["response"] = "[NO RESPONSE - TIMEOUT]"
            # After timeout, wait and drain any late responses to prevent
            # them from being picked up by the NEXT chat() call (1-message cascade)
            await asyncio.sleep(3)
            await self._drain()

        return result

    def record(self, category: str, prompt: str, resp: Dict, passed: bool, reason: str = ""):
        self.results.append({
            "category": category,
            "prompt": prompt,
            "answer": resp.get("response", ""),
            "intent": resp.get("intent", ""),
            "action": resp.get("action", ""),
            "passed": passed,
            "reason": reason,
        })
        icon = f"{C.GREEN}PASS{C.RESET}" if passed else f"{C.RED}FAIL{C.RESET}"
        reason_str = f" | {C.RED}{reason}{C.RESET}" if reason and not passed else ""
        print(f"  {C.GRAY}{ts()}{C.RESET}  {icon}  {C.DIM}[{category}]{C.RESET} {prompt[:60]}{reason_str}")

    async def close(self):
        if self._listener_task:
            self._listener_task.cancel()
        if self.ws:
            await self.ws.close()
        self.connected = False

    def print_report(self):
        """Print full detailed report: prompt vs answer."""
        total = len(self.results)
        passed = sum(1 for r in self.results if r["passed"])

        print(f"\n  {C.BOLD}{'=' * 90}{C.RESET}")
        print(f"  {C.BOLD}{C.CYAN}  FULL TEST REPORT — {passed}/{total} Passed{C.RESET}")
        print(f"  {C.BOLD}{'=' * 90}{C.RESET}")

        # Group by category
        categories = {}
        for r in self.results:
            cat = r["category"]
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(r)

        test_num = 0
        for cat, tests in categories.items():
            cat_passed = sum(1 for t in tests if t["passed"])
            cat_color = C.GREEN if cat_passed == len(tests) else C.RED
            print(f"\n  {C.BOLD}{C.YELLOW}  [{cat}] — {cat_color}{cat_passed}/{len(tests)} passed{C.RESET}")
            print(f"  {C.DIM}{'─' * 88}{C.RESET}")

            for t in tests:
                test_num += 1
                icon = f"{C.GREEN}PASS{C.RESET}" if t["passed"] else f"{C.RED}FAIL{C.RESET}"
                fail_reason = f"\n  {C.RED}     Reason: {t['reason']}{C.RESET}" if t["reason"] and not t["passed"] else ""

                # Truncate answer for display
                answer = t["answer"].replace("\n", " ").strip()
                if len(answer) > 300:
                    answer = answer[:300] + "..."

                print(f"\n  {icon}  {C.BOLD}#{test_num}{C.RESET}")
                print(f"  {C.CYAN}     Prompt:{C.RESET}  {t['prompt']}")
                print(f"  {C.GREEN}     Answer:{C.RESET}  {answer}")
                print(f"  {C.DIM}     Intent: {t['intent']}  |  Action: {t['action']}{C.RESET}{fail_reason}")

        # Final summary
        print(f"\n  {C.BOLD}{'=' * 90}{C.RESET}")
        color = C.GREEN if passed == total else C.YELLOW if passed > total * 0.7 else C.RED
        print(f"  {C.BOLD}{color}  TOTAL: {passed}/{total} tests passed ({passed*100//total}%){C.RESET}")

        # Failed tests quick list
        failed = [r for r in self.results if not r["passed"]]
        if failed:
            print(f"\n  {C.RED}{C.BOLD}  Failed Tests:{C.RESET}")
            for i, f_test in enumerate(failed, 1):
                print(f"    {C.RED}{i}. [{f_test['category']}] {f_test['prompt'][:70]}{C.RESET}")
                if f_test["reason"]:
                    print(f"       {C.DIM}Reason: {f_test['reason']}{C.RESET}")

        print(f"  {C.BOLD}{'=' * 90}{C.RESET}\n")


# ─── TEST PROMPTS (4 categories: Casual, General, Policy, Hard Multi-Q) ──

async def test_casual(agent: WSTestAgent):
    """10 casual/friendly chat prompts — tests off-topic answer-then-redirect."""
    cat = "Casual"
    print(f"\n  {C.BOLD}{C.MAGENTA}>> Testing: {cat} (10 prompts){C.RESET}\n")

    prompts = [
        ("Hey, how are you?", "Should greet back and redirect to insurance"),
        ("Kya chal raha hai bhai?", "Should reply casually and redirect"),
        ("I'm bored, tell me something fun", "Should engage briefly then redirect"),
        ("Good morning!", "Should greet and redirect to insurance topics"),
        ("Tell me a joke", "Should tell a joke then redirect"),
        ("What's up?", "Should respond casually and redirect"),
        ("I had a really bad day today", "Should empathize then redirect to insurance"),
        ("Can you suggest a good movie?", "Should suggest briefly then redirect"),
        ("Bro do you sleep?", "Should answer briefly then redirect"),
        ("Tu meri baat samajhta hai?", "Should respond yes and redirect to insurance"),
    ]

    for prompt, expected in prompts:
        resp = await agent.chat(prompt)
        has_answer = bool(resp["response"]) and resp["type"] != "timeout"
        # Should NOT block with "that's not my area"
        is_blocked = any(kw in resp["response"].lower() for kw in
                         ["i can only help with", "that's not my area", "i'm not able to"])
        # Should mention insurance/policy/finance somewhere (redirect)
        has_redirect = any(w in resp["response"].lower() for w in
                           ["insurance", "policy", "finance", "coverage", "premium", "bima", "protect"])
        agent.record(cat, prompt, resp, has_answer and not is_blocked,
                     "Blocked off-topic instead of answering" if is_blocked else
                     (f"Expected: {expected}" if not has_answer else ""))
        await asyncio.sleep(0.5)


async def test_general(agent: WSTestAgent):
    """10 general knowledge prompts — tests answer-then-redirect behavior."""
    cat = "General"
    print(f"\n  {C.BOLD}{C.MAGENTA}>> Testing: {cat} (10 prompts){C.RESET}\n")

    prompts = [
        ("Who is the prime minister of India?", "Should answer Modi then redirect"),
        ("What is the capital of France?", "Should answer Paris then redirect"),
        ("Explain what AI is in simple words", "Should explain AI briefly then redirect"),
        ("What's the weather like in Mumbai?", "Should attempt answer then redirect"),
        ("How many states are there in India?", "Should answer 28 then redirect"),
        ("Who won the last IPL?", "Should answer briefly then redirect"),
        ("What is cryptocurrency?", "Should explain briefly then redirect"),
        ("Who invented the telephone?", "Should answer Alexander Graham Bell then redirect"),
        ("What is the full form of GST?", "Should answer Goods and Services Tax then redirect"),
        ("Python better hai ya Java?", "Should give brief opinion then redirect"),
    ]

    for prompt, expected in prompts:
        resp = await agent.chat(prompt)
        has_answer = bool(resp["response"]) and resp["type"] != "timeout"
        is_blocked = any(kw in resp["response"].lower() for kw in
                         ["i can only help with", "that's not my area", "i'm not able to"])
        agent.record(cat, prompt, resp, has_answer and not is_blocked,
                     "Blocked off-topic instead of answering" if is_blocked else
                     (f"Expected: {expected}" if not has_answer else ""))
        await asyncio.sleep(0.5)


async def test_policy(agent: WSTestAgent):
    """20 policy-related questions — tests insurance domain knowledge and data retrieval."""
    cat = "Policy"
    print(f"\n  {C.BOLD}{C.MAGENTA}>> Testing: {cat} (20 prompts){C.RESET}\n")

    prompts = [
        ("Show me all my policies", "Should list user's policies"),
        ("meri health insurance policy ka status kya hai?", "Should show health policy status"),
        ("When does my policy expire?", "Should give expiry date"),
        ("What is my sum insured?", "Should give coverage amount"),
        ("Who is the nominee on my policy?", "Should give nominee info"),
        ("Claim kaise file karu?", "Should explain claim process"),
        ("What's the waiting period for pre-existing diseases?", "Should explain waiting period"),
        ("Can I port my policy to another insurer?", "Should explain portability"),
        ("How much premium am I paying?", "Should give premium details"),
        ("Is my family covered under my policy?", "Should check family coverage"),
        ("What happens if I miss a premium payment?", "Should explain lapse consequences"),
        ("Meri policy ka renewal kab hai?", "Should give renewal date"),
        ("Compare my policies", "Should compare user's policies"),
        ("Am I covered for hospitalization?", "Should check health coverage"),
        ("What tax benefits do I get from insurance?", "Should explain Section 80D/80C"),
        ("How to add a rider to my policy?", "Should explain rider addition"),
        ("My claim got rejected, what do I do?", "Should guide on rejected claim"),
        ("What's the claim settlement ratio of my insurer?", "Should give CSR info"),
        ("Should I increase my sum insured?", "Should give recommendation"),
        ("Policy document kaha se download karu?", "Should guide to policy locker/download"),
    ]

    for prompt, expected in prompts:
        resp = await agent.chat(prompt)
        has_answer = bool(resp["response"]) and resp["type"] != "timeout"
        # Should NOT give generic navigation for specific questions
        is_nav = any(kw in resp["response"].lower() for kw in
                     ["self or family", "whose policies", "select who", "which do you want to check"])
        agent.record(cat, prompt, resp, has_answer and not is_nav,
                     f"Got navigation instead of answer" if is_nav else
                     (f"Expected: {expected}" if not has_answer else ""))
        await asyncio.sleep(0.5)


async def test_hard_multi(agent: WSTestAgent):
    """20 hard multi-question prompts — multiple questions in a single message."""
    cat = "Hard Multi-Q"
    print(f"\n  {C.BOLD}{C.MAGENTA}>> Testing: {cat} (20 prompts){C.RESET}\n")

    prompts = [
        (
            "What is my sum insured and when does my policy expire?",
            "sum insured|coverage|expire|expiry|renewal|amount",
            "Should answer both: sum insured AND expiry"
        ),
        (
            "Meri kitni policies hai aur konsi expire hone wali hai?",
            "policy|policies|expire|expiry|renewal",
            "Should answer count AND upcoming expiry"
        ),
        (
            "Compare my health and auto insurance, which one is better?",
            "health|auto|car|vehicle|compare|better",
            "Should compare both policy types"
        ),
        (
            "Tell me about term insurance, and also do I have one?",
            "term|life|insurance|policy|have|don't",
            "Should explain term insurance AND check user's policies"
        ),
        (
            "What is the claim process and how long does it usually take?",
            "claim|process|step|time|days|duration",
            "Should explain process AND timeline"
        ),
        (
            "Can I add my wife as nominee and also increase the coverage?",
            "nominee|wife|add|coverage|increase|sum insured",
            "Should answer both: nominee change AND coverage increase"
        ),
        (
            "Premium kitna hai mera aur kya koi discount milega?",
            "premium|amount|discount|offer",
            "Should give premium AND discuss discounts"
        ),
        (
            "What is critical illness cover, does my policy have it, and should I get it?",
            "critical illness|cancer|heart|cover|policy|recommend",
            "Should explain, check, AND recommend"
        ),
        (
            "Kya health insurance aur life insurance dono zaroori hai? Aur mere paas dono hai kya?",
            "health|life|insurance|both|zaroori|necessary|policy",
            "Should explain importance AND check user policies"
        ),
        (
            "I want to know my policy number, the insurer name, and when I bought it",
            "policy number|insurer|company|date|bought|start",
            "Should provide all three details"
        ),
        (
            "What's the difference between term and whole life insurance and which is cheaper?",
            "term|whole life|difference|cheaper|cost|premium",
            "Should compare both AND mention cost"
        ),
        (
            "My father needs hospitalization, am I covered for that and what documents do I need?",
            "hospital|cover|document|father|family|claim",
            "Should check coverage AND list documents"
        ),
        (
            "Show my expired policies, tell me if I should renew them, and what's the penalty for late renewal",
            "expire|renew|penalty|late|grace period",
            "Should show expired, advise renewal, AND explain penalty"
        ),
        (
            "How do cashless claims work and which hospitals near me accept it?",
            "cashless|hospital|network|claim|accept",
            "Should explain cashless AND mention network hospitals"
        ),
        (
            "I want to port my policy, is it a good idea, and how long does it take?",
            "port|transfer|switch|time|days|process",
            "Should advise on porting AND mention timeline"
        ),
        (
            "What all riders do I have, are they worth the money, and can I remove any?",
            "rider|add-on|worth|remove|benefit",
            "Should list riders, evaluate AND advise on removal"
        ),
        (
            "Tell me about the eazr rewards program and how many policies do I need to upload for the free PA insurance?",
            "reward|upload|pa insurance|free|policy|5",
            "Should explain rewards AND mention 5-policy requirement"
        ),
        (
            "Calculate my protection score, tell me what's pulling it down, and how to improve it",
            "protection score|score|improve|low|factor|gap",
            "Should give score, weakness, AND improvement tips"
        ),
        (
            "Bhai meri family ke liye best health plan kaunsa hai, kitna cover hona chahiye, aur monthly kitna padega?",
            "family|health|plan|cover|lakh|monthly|premium",
            "Should recommend plan, coverage amount, AND approximate premium"
        ),
        (
            "What is the difference between copay and deductible, does my policy have either, and should I be worried?",
            "copay|deductible|policy|difference|worry",
            "Should explain both terms, check policy, AND advise"
        ),
    ]

    for prompt, expected_words, expected_desc in prompts:
        resp = await agent.chat(prompt)
        has_answer = bool(resp["response"]) and resp["type"] != "timeout"
        expected_list = expected_words.split("|")
        # For multi-Q, at least 2 relevant words should appear (answering multiple parts)
        matching_words = [w for w in expected_list if w in resp["response"].lower()]
        has_multi_answer = len(matching_words) >= 2
        agent.record(cat, prompt, resp, has_answer and has_multi_answer,
                     f"Only addressed partially. Expected: {expected_desc}" if not has_multi_answer else "")
        await asyncio.sleep(0.8)


# ─── Interactive Mode ──────────────────────────────────────────────────────

async def interactive_mode(agent: WSTestAgent):
    print(f"\n  {C.BOLD}{C.CYAN}Interactive Chat Mode{C.RESET}")
    print(f"  Type messages. Commands: /quit /ping /history\n")

    while agent.connected:
        try:
            user_input = await asyncio.get_event_loop().run_in_executor(
                None, lambda: input(f"  {C.CYAN}You>{C.RESET} ")
            )
        except (EOFError, KeyboardInterrupt):
            break

        user_input = user_input.strip()
        if not user_input:
            continue
        if user_input == "/quit":
            break
        if user_input == "/ping":
            await agent.ws.send(json.dumps({"type": "ping"}))
            pong = await agent._wait_for("pong", timeout=5)
            print(f"    Pong: {'received' if pong else 'timeout'}")
            continue
        if user_input == "/history":
            for r in agent.results[-10:]:
                icon = f"{C.GREEN}P{C.RESET}" if r["passed"] else f"{C.RED}F{C.RESET}"
                print(f"    {icon} [{r['intent']}] {r['prompt'][:50]} -> {r['answer'][:60]}")
            continue

        resp = await agent.chat(user_input)
        print(f"\n    {C.GREEN}Bot:{C.RESET} {resp['response']}")
        print(f"    {C.DIM}Intent: {resp['intent']}  |  Action: {resp['action']}{C.RESET}\n")


# ─── Runner ────────────────────────────────────────────────────────────────

ALL_TESTS = {
    "casual": ("Casual Chat (10)", test_casual),
    "general": ("General Knowledge (10)", test_general),
    "policy": ("Policy Questions (20)", test_policy),
    "hard": ("Hard Multi-Question (20)", test_hard_multi),
}


async def run_tests(url: str, token: str, test_names: Optional[List[str]] = None):
    agent = WSTestAgent(url=url, token=token)

    try:
        if not await agent.connect():
            print(f"  {C.RED}Cannot connect. Aborting.{C.RESET}")
            return

        tests_to_run = test_names or list(ALL_TESTS.keys())

        for name in tests_to_run:
            if name not in ALL_TESTS:
                print(f"  {C.RED}Unknown test: {name}{C.RESET}")
                print(f"  Available: {', '.join(ALL_TESTS.keys())}")
                continue
            label, func = ALL_TESTS[name]
            await func(agent)

        agent.print_report()

    finally:
        await agent.close()


async def run_interactive(url: str, token: str):
    agent = WSTestAgent(url=url, token=token)
    try:
        if not await agent.connect():
            return
        await interactive_mode(agent)
    finally:
        await agent.close()


def show_menu():
    print(f"\n  {C.BOLD}{'=' * 50}{C.RESET}")
    print(f"  {C.BOLD}{C.CYAN}  EAZR WebSocket Test Agent{C.RESET}")
    print(f"  {C.BOLD}{'=' * 50}{C.RESET}")
    print(f"\n    {C.BOLD}1{C.RESET})  Run ALL tests (4 categories, 60 prompts)")
    print(f"    {C.BOLD}2{C.RESET})  Interactive chat mode")
    for i, (key, (label, _)) in enumerate(ALL_TESTS.items(), 3):
        print(f"    {C.BOLD}{i}{C.RESET})  {label}")
    print(f"    {C.BOLD}0{C.RESET})  Exit\n")


def main():
    parser = argparse.ArgumentParser(description="EAZR WebSocket Hard Test Agent")
    parser.add_argument("--url", default="ws://localhost:8000/ws/chat")
    parser.add_argument("--token", required=True, help="JWT access token")
    parser.add_argument("--test", default=None, help=f"Run specific: {', '.join(ALL_TESTS.keys())}")
    parser.add_argument("--all", action="store_true", help="Run all tests")
    parser.add_argument("--interactive", "-i", action="store_true", help="Interactive mode")

    args = parser.parse_args()
    token = args.token

    if args.all:
        asyncio.run(run_tests(args.url, token))
        return
    elif args.interactive:
        asyncio.run(run_interactive(args.url, token))
        return
    elif args.test:
        tests = [t.strip() for t in args.test.split(",")]
        asyncio.run(run_tests(args.url, token, tests))
        return

    # Menu
    test_keys = list(ALL_TESTS.keys())
    while True:
        show_menu()
        try:
            choice = input(f"  {C.CYAN}Select>{C.RESET} ").strip()
        except (EOFError, KeyboardInterrupt):
            break

        if choice == "0":
            break
        elif choice == "1":
            asyncio.run(run_tests(args.url, token))
        elif choice == "2":
            asyncio.run(run_interactive(args.url, token))
        else:
            try:
                idx = int(choice) - 3
                if 0 <= idx < len(test_keys):
                    asyncio.run(run_tests(args.url, token, [test_keys[idx]]))
                else:
                    print(f"  Invalid choice")
            except ValueError:
                print(f"  Invalid choice")


if __name__ == "__main__":
    main()
