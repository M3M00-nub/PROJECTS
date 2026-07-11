
"""
STOPTHEGEEK - Smart Spending Agent
Personal Expense Analyzer with logging support
Author: Jorge Guillermo Farfán Zapata | UPY | Matricula: 2509079
"""

import logging
import os
from datetime import datetime

# ──────────────────────────────────────────────
#  LOGGING SETUP
# ──────────────────────────────────────────────

os.makedirs("logs", exist_ok=True)

log_filename = f"logs/{datetime.now().strftime('%Y-%m-%d')}.log"

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s — [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.FileHandler(log_filename, encoding="utf-8"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("stopthegeek")

# ──────────────────────────────────────────────
#  CATEGORY MAP
# ──────────────────────────────────────────────

CATEGORIES = {
    "1": "Food",
    "2": "Transportation",
    "3": "Education",
    "4": "Entertainment",
    "5": "Health",
    "6": "Bills and Services",
    "7": "Personal Expenses",
    "8": "Other"
}

RECOMMENDATIONS = {
    "Food":               "Consider meal prepping at home to reduce food expenses and food waste.",
    "Transportation":     "Consider using public transit or carpooling to cut costs and reduce your carbon footprint.",
    "Education":          "Look for free or open-access resources online to complement paid materials.",
    "Entertainment":      "Try free local events or rotate streaming subscriptions to lower entertainment costs.",
    "Health":             "Preventive habits (exercise, sleep) can reduce long-term health expenses.",
    "Bills and Services": "Review your subscriptions and consider energy-saving habits to lower utility bills.",
    "Personal Expenses":  "Track discretionary spending weekly to identify patterns and cut unnecessary purchases.",
    "Other":              "Review uncategorized expenses — recurring ones might deserve their own category."
}

WARN_THRESHOLD = 0.80   # 80 % of budget → warning
REC_THRESHOLD  = 0.50   # 50 % spent in one category → recommendation

# ──────────────────────────────────────────────
#  HELPERS
# ──────────────────────────────────────────────

def get_float(prompt: str) -> float:
    """Read a positive float from the user, retry on invalid input."""
    while True:
        raw = input(prompt).strip()
        try:
            value = float(raw)
            if value <= 0:
                raise ValueError("Value must be positive")
            return value
        except ValueError:
            logger.warning("Invalid numeric input received: '%s' — retrying", raw)
            print("  ⚠ Please enter a valid positive number.\n")


def get_category() -> str:
    """Display category menu and return the chosen category name."""
    print("\nSelect the expense category:")
    for key, name in CATEGORIES.items():
        print(f"  {key} - {name}")

    while True:
        choice = input("Your choice (1-8): ").strip()
        if choice in CATEGORIES:
            return CATEGORIES[choice]
        logger.warning("Invalid category selection: '%s' — retrying", choice)
        print("  ⚠ Enter a number between 1 and 8.\n")


def show_summary(user: str, budget: float, total: float,
                 remaining: float, status: str, amount: float, category: str) -> None:
    """Print the per-expense summary to the console."""
    pct = (remaining * 100) / budget if budget else 0
    print("\n" + "=" * 45)
    print(f"  User Name  : {user}")
    print(f"  Category   : {category}")
    print(f"  Spent now  : ${amount:,.2f}")
    print(f"  Total spent: ${total:,.2f}")
    print(f"  Remaining  : ${remaining:,.2f}  ({pct:.1f}% left)")
    print(f"  Status     : {status}")
    print("=" * 45)


# ──────────────────────────────────────────────
#  AGENT LOGIC  (perceive → decide → act)
# ──────────────────────────────────────────────

def evaluate_and_recommend(category: str, amount: float,
                            total: float, budget: float,
                            category_totals: dict) -> str:
    """
    Perceive spending data, decide if action is needed,
    and return an actionable recommendation string (or empty string).
    """
    cat_total = category_totals.get(category, 0)
    cat_ratio = cat_total / total if total else 0

    if cat_ratio >= REC_THRESHOLD:
        recommendation = RECOMMENDATIONS[category]
        logger.info(
            "Agent recommendation triggered — category '%s' is %.0f%% of total spending: %s",
            category, cat_ratio * 100, recommendation
        )
        return recommendation
    return ""


# ──────────────────────────────────────────────
#  MAIN PROGRAM
# ──────────────────────────────────────────────

def main() -> None:
    logger.info("=== STOPTHEGEEK session started ===")

    print("\n" + "=" * 45)
    print("   STOPTHEGEEK — Smart Spending Agent")
    print("=" * 45)

    # ── Initial inputs ──
    user_name = input("Enter your name: ").strip()
    if not user_name:
        user_name = "User"
        logger.warning("No name provided — defaulting to 'User'")

    budget = get_float("Enter your monthly budget ($): ")
    logger.info("Session started for user '%s' with budget $%.2f", user_name, budget)

    total_expenses   = 0.0
    category_totals  = {}   # track spending per category
    expense_count    = 0

    # ── Main loop ──
    while True:
        print()
        category  = get_category()
        amount    = get_float(f"Enter the amount spent in {category} ($): ")

        # Accumulate
        total_expenses              += amount
        category_totals[category]    = category_totals.get(category, 0) + amount
        expense_count               += 1
        remaining                    = budget - total_expenses

        logger.info(
            "Expense #%d registered — category: '%s', amount: $%.2f, "
            "running total: $%.2f, remaining: $%.2f",
            expense_count, category, amount, total_expenses, remaining
        )

        # ── Status decision ──
        if total_expenses > budget:
            status = "⚠  Budget EXCEEDED"
            logger.error(
                "Budget exceeded! Total $%.2f > Budget $%.2f (over by $%.2f)",
                total_expenses, budget, total_expenses - budget
            )
        elif total_expenses >= budget * WARN_THRESHOLD:
            status = "⚡ Approaching limit (80 %+ used)"
            logger.warning(
                "80%% budget threshold reached — total $%.2f of $%.2f",
                total_expenses, budget
            )
        else:
            status = "✓  Budget under control"

        show_summary(user_name, budget, total_expenses,
                     remaining, status, amount, category)

        # ── Agent recommendation ──
        tip = evaluate_and_recommend(
            category, amount, total_expenses, budget, category_totals
        )
        if tip:
            print(f"\n  💡 Agent tip: {tip}")

        # ── Continue? ──
        again = input("\nRegister another expense? (S/N): ").strip().upper()
        if again != "S":
            logger.info("User chose to end session after %d expense(s)", expense_count)
            break

    # ── Monthly summary ──
    savings_pct = (remaining * 100 / budget) if budget else 0

    print("\n" + "=" * 45)
    print("          MONTHLY SUMMARY")
    print("=" * 45)
    print(f"  User          : {user_name}")
    print(f"  Total budget  : ${budget:,.2f}")
    print(f"  Total expenses: ${total_expenses:,.2f}")
    print(f"  Remaining     : ${remaining:,.2f}")
    print(f"  Savings %     : {savings_pct:.1f}%")
    print(f"  Final status  : {status}")
    print("\n  Expenses by category:")
    for cat, val in sorted(category_totals.items(), key=lambda x: -x[1]):
        pct = (val / total_expenses * 100) if total_expenses else 0
        print(f"    {cat:<22} ${val:>8,.2f}  ({pct:.0f}%)")
    print("=" * 45)

    logger.info(
        "=== Session ended — total expenses: $%.2f / $%.2f | status: %s ===",
        total_expenses, budget, status.strip()
    )


if __name__ == "__main__":
    main()
