
#!/usr/bin/env python3
import argparse
import sqlite3
import sys
import textwrap
from pathlib import Path

DB_FILE = Path(__file__).parents[1] / "db" / "pomodoros.sqlite"

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
            print(f"[!] Error: Project code '{args.code.upper()}' does not exist.", file=sys.stderr)
            sys.exit(1)

        project_id = proj["project_id"]
        project_name = proj["project_name"]

        # 2. Validate anchor vs continuation rules
        if args.parent is None and not args.name:
            print("[!] Error: A new task (--name) is required when starting an anchor row (no --parent).", file=sys.stderr)
            sys.exit(1)

        # 3. Insert Pomodoro session record with ALL metadata dimensions
        cur.execute(
            """
            INSERT INTO pomodoros (
                project_id,
                pomo_id_parent,
                priority,
                pomo_name,
                poms_planned,
                poms_achieved,
                poms_interrupted,
                pomo_effort,
                pomo_energy,
                pomo_interrupt_type,
                pomo_friction,
                notes,
                pomo_complete       -- Correctly flags if the task is fully done
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                project_id,
                args.parent,
                args.priority,
                args.name if args.parent is None else None,
                args.plan,
                args.completed,     # Maps to poms_achieved
                args.interrupt,
                args.effort,
                args.energy,
                args.interrupt_type,
                args.friction,
                args.notes,
                1 if args.done else 0, # Maps to pomo_complete
            ),
        )

        new_id = cur.lastrowid
        conn.commit()

        # 4. Immediate Terminal Feedback
        total_mins = args.completed * 25
        hours = round(total_mins / 60.0, 2)

        print(f"\n[+] Logged Session #{new_id} -> {args.code.upper()} ({project_name})")
        if args.parent:
            print(f"    Linked to Anchor Task #{args.parent}")
        else:
            print(f"    Anchor Task: \"{args.name}\"")

        print(f"    Execution: {args.completed} completed | {args.interrupt} interrupted | {args.plan} planned (~{hours} hrs)")

        # Display diagnostic metadata if it deviates from perfect flow
        diagnostics = []
        diagnostics.append(f"RPE: E{args.effort}")
        if args.energy != 'NORMAL':
            diagnostics.append(f"Energy: {args.energy}")
        if args.friction != 'FLOW':
            diagnostics.append(f"Friction: {args.friction}")
        if args.interrupt > 0 or args.interrupt_type != 'NONE':
            diagnostics.append(f"Leak: {args.interrupt_type}")

        print(f"    Telemetry: [{', '.join(diagnostics)}]")

        if args.notes:
            print(f"    AAR Note : {args.notes}")
        if args.done:
            print("    Status   : [✓ MARKED COMPLETE]")
        print()

def show_summary():
    with get_db() as conn:
        cur = conn.cursor()
        query = """
        SELECT 
            COALESCE(s.pomo_id_parent, s.pomo_id) AS root_id,
            MIN(s.priority) AS root_priority,
            COALESCE(parent.pomo_name, s.pomo_name) AS deliverable,
            p.project_code,
            SUM(s.poms_achieved) AS total_completed,
            ROUND(AVG(s.pomo_effort), 1) AS avg_effort,
            MAX(s.pomo_complete) AS is_done,
            ROUND(SUM(s.poms_achieved * s.pom_mins) / 60.0, 2) AS focus_hours
        FROM pomodoros s
        JOIN projects p ON s.project_id = p.project_id
        LEFT JOIN pomodoros parent ON s.pomo_id_parent = parent.pomo_id
        GROUP BY root_id
        ORDER BY is_done ASC, root_priority ASC, root_id DESC;
        """
        rows = cur.execute(query).fetchall()

        if not rows:
            print("\nNo pomodoro sessions logged yet.\n")
            return

        print("\n" + "=" * 94)
        print(f"{'ID':<5} {'PRI':<3} {'PROJECT':<12} {'DELIVERABLE':<30} {'POMS':<6} {'HOURS':<7} {'AVG E#':<8} {'STATUS'}")
        print("-" * 94)
        
        for r in rows:
            status = "✓ Done" if r["is_done"] else "In Progress"
            wrapped_deliv = textwrap.wrap(r["deliverable"], width=30) or [""]
            
            # Print the main row with the 'P' prefix for the priority integer
            print(f"#{r['root_id']:<4} P{r['root_priority']:<2} {r['project_code']:<12} {wrapped_deliv[0]:<30} {r['total_completed']:<6} {r['focus_hours']:<7} {r['avg_effort']:<8} {status}")
            
            # Print any extra text-wrapped lines with proper blank spacing for ID, PRI, and PROJECT
            for extra_line in wrapped_deliv[1:]:
                print(f"{'':<5} {'':<3} {'':<12} {extra_line:<30}")
                
        print("=" * 94 + "\n")

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
    parser = argparse.ArgumentParser(description="Lightning Pomodoro CLI Logger for SQLite")

    # Informational flags
    parser.add_argument("-s", "--summary", action="store_true", help="Display consolidated task rollup table")
    parser.add_argument("-p", "--projects", action="store_true", help="List active project codes")

    # Core Execution Arguments
    parser.add_argument("-c", "--code", type=str, help="Project code (e.g., NET-10G)")
    parser.add_argument("-n", "--name", type=str, help="Task name (required for anchor row)")
    parser.add_argument("--parent", type=int, default=None, help="Parent task ID if continuing a prior task")
    parser.add_argument("--priority", type=int, choices=[1, 2, 3, 4], default=4, help="Pomodoro priority (1=Highest, 4=Lowest, default: 4)")
    parser.add_argument("--plan", type=int, default=1, help="Poms planned (circles drawn, default: 1)")
    parser.add_argument("--completed", type=int, default=1, help="Poms completed (dots filled, default: 1)")
    parser.add_argument("-i", "--interrupt", type=int, default=0, help="Poms interrupted (crossed out, default: 0)")
    parser.add_argument("-d", "--done", action="store_true", help="Flag deliverable fully complete")

    # Metadata Diagnostic Arguments
    parser.add_argument("-e", "--effort", type=int, choices=range(1, 6), default=3, help="Cognitive effort / RPE (1=mechanical, 5=crucible, default: 3)")
    parser.add_argument("--energy", type=str.upper, choices=['LOW', 'NORMAL', 'PEAK'], default='NORMAL', help="Biological state going into the block (default: NORMAL)")
    parser.add_argument("--interrupt-type", type=str.upper, choices=['NONE', 'INTERNAL', 'EXTERNAL'], default='NONE', help="Source of the disruption (default: NONE)")
    parser.add_argument("--friction", type=str.upper, choices=['FLOW', 'TOOLING', 'AMBIGUOUS', 'DEPENDENCY'], default='FLOW', help="Root cause of execution drag (default: FLOW)")
    parser.add_argument("-m", "--notes", type=str, default=None, help="Micro-AAR (e.g., 'Friction | Fix or Artifact')")

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