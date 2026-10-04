
#!/usr/bin/env python3
import argparse
import sqlite3
import sys
from pathlib import Path

DB_FILE = Path(__file__).parent / "pomodoro_tracker.db"


def get_db():
    conn = sqlite3.connect(DB_FILE)
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.row_factory = sqlite3.Row
    return conn


def log_session(args):
    with get_db() as conn:
        cur = conn.cursor()

        # 1. Resolve project_code to project_id
        cur.execute(
            "SELECT project_id, project_name FROM projects WHERE project_code = ?",
            (args.code.upper(),),
        )
        proj = cur.fetchone()
        if not proj:
            print(
                f"[!] Error: Project code '{args.code.upper()}' does not exist.",
                file=sys.stderr,
            )
            print(
                "    Create it first or check available codes with: python tracker.py --projects",
                file=sys.stderr,
            )
            sys.exit(1)

        project_id = proj["project_id"]
        project_name = proj["project_name"]

        # 2. Validate anchor vs continuation rules
        if args.parent is None and not args.name:
            print(
                "[!] Error: A new task (--name) is required when starting an anchor row (no --parent).",
                file=sys.stderr,
            )
            sys.exit(1)

        # 3. Insert Pomodoro session record
        cur.execute(
            """
            INSERT INTO pomodoros (
                project_id,
                pomo_id_parent,
                pomo_name,
                poms_planned,
                poms_completed,
                poms_interrupted,
                notes,
                pomo_complete
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                project_id,
                args.parent,
                args.name if args.parent is None else None,
                args.plan,
                args.done,
                args.interrupt,
                args.notes,
                1 if args.complete else 0,
            ),
        )

        new_id = cur.lastrowid
        conn.commit()

        # 4. Immediate Terminal Feedback
        total_mins = args.done * 25
        hours = round(total_mins / 60.0, 2)
        print(f"\n[+] Logged Session #{new_id} -> {args.code.upper()} ({project_name})")
        if args.parent:
            print(f"    Linked to Anchor Task #{args.parent}")
        else:
            print(f"    Anchor Task: \"{args.name}\"")
        print(
            f"    Stats: {args.done} completed | {args.interrupt} interrupted | {args.plan} planned (~{hours} hrs)"
        )
        if args.complete:
            print("    Status: [✓ MARKED COMPLETE]")
        print()


def show_summary():
    with get_db() as conn:
        cur = conn.cursor()
        query = """
        SELECT
            COALESCE(s.pomo_id_parent, s.pomo_id) AS root_id,
            COALESCE(parent.pomo_name, s.pomo_name) AS deliverable,
            p.project_code,
            MIN(s.pomo_created) AS first_logged,
            MAX(s.pomo_created) AS last_logged,
            SUM(s.poms_completed) AS total_completed,
            SUM(s.poms_interrupted) AS total_interrupted,
            MAX(s.pomo_complete) AS is_done,
            ROUND(SUM(s.poms_completed * s.pom_mins) / 60.0, 2) AS focus_hours
        FROM pomodoros s
        JOIN projects p ON s.project_id = p.project_id
        LEFT JOIN pomodoros parent ON s.pomo_id_parent = parent.pomo_id
        GROUP BY root_id
        ORDER BY is_done ASC, root_id DESC;
        """
        rows = cur.execute(query).fetchall()

        if not rows:
            print("\nNo pomodoro sessions logged yet.\n")
            return

        print("\n" + "=" * 80)
        print(
            f"{'ID':<5} {'PROJECT':<12} {'DELIVERABLE':<32} {'POMS':<8} {'HOURS':<8} {'STATUS'}"
        )
        print("-" * 80)
        for r in rows:
            status = "✓ Done" if r["is_done"] else "In Progress"
            deliv = (
                (r["deliverable"][:29] + "...")
                if len(r["deliverable"]) > 32
                else r["deliverable"]
            )
            print(
                f"#{r['root_id']:<4} {r['project_code']:<12} {deliv:<32} {r['total_completed']:<8} {r['focus_hours']:<8} {status}"
            )
        print("=" * 80 + "\n")


def list_projects():
    with get_db() as conn:
        cur = conn.cursor()
        rows = cur.execute(
            """
            SELECT project_code, project_name, project_priority, project_status, weekly_pom_budget
            FROM projects
            ORDER BY project_status, project_priority;
        """
        ).fetchall()

        print("\n" + "=" * 65)
        print(
            f"{'CODE':<12} {'PRIORITY':<10} {'STATUS':<10} {'BUDGET':<8} {'NAME'}"
        )
        print("-" * 65)
        for r in rows:
            print(
                f"{r['project_code']:<12} {r['project_priority']:<10} {r['project_status']:<10} {r['weekly_pom_budget']:<8} {r['project_name']}"
            )
        print("=" * 65 + "\n")


def main():
    parser = argparse.ArgumentParser(
        description="Lightning Pomodoro CLI Logger for SQLite"
    )

    # Informational flags
    parser.add_argument(
        "-s",
        "--summary",
        action="store_true",
        help="Display consolidated task rollup table",
    )
    parser.add_argument(
        "-p", "--projects", action="store_true", help="List active project codes"
    )

    # Ingestion arguments
    parser.add_argument("-c", "--code", type=str, help="Project code (e.g., NET-10G)")
    parser.add_argument(
        "-n", "--name", type=str, help="Task name (required for anchor row)"
    )
    parser.add_argument(
        "--plan", type=int, default=1, help="Poms planned (circles drawn, default: 1)"
    )
    parser.add_argument(
        "-d",
        "--done",
        type=int,
        default=1,
        help="Poms completed (dots filled, default: 1)",
    )
    parser.add_argument(
        "-i",
        "--interrupt",
        type=int,
        default=0,
        help="Poms interrupted (crossed out, default: 0)",
    )
    parser.add_argument(
        "--parent",
        type=int,
        default=None,
        help="Parent task ID if continuing a prior task",
    )
    parser.add_argument(
        "--complete", action="store_true", help="Flag deliverable fully complete"
    )
    parser.add_argument(
        "-m", "--notes", type=str, default=None, help="Brief outcome or blocker note"
    )

    args = parser.parse_args()

    if args.summary:
        show_summary()
    elif args.projects:
        list_projects()
    elif args.code:
        log_session(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()