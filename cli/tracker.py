
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

def list_objectives():
    with get_db() as conn:
        cur = conn.cursor()
        rows = cur.execute(
            """
            SELECT objective_id, crucible_id, objective_status, objective_target_date, objective_title
            FROM objectives
            ORDER BY objective_status ASC, objective_target_date ASC;
            """
        ).fetchall()

        print("\n" + "=" * 80)
        print(f"{'ID':<5} {'CRUCIBLE':<10} {'STATUS':<12} {'TARGET DATE':<12} {'TITLE'}")
        print("-" * 80)
        for r in rows:
            crucible = r['crucible_id'] if r['crucible_id'] else "None"
            target = r['objective_target_date'] if r['objective_target_date'] else "None"
            print(f"#{r['objective_id']:<4} {crucible:<10} {r['objective_status']:<12} {target:<12} {r['objective_title']}")
        print("=" * 80 + "\n")

def add_objective(args):
    with get_db() as conn:
        cur = conn.cursor()
        try:
            # Matches the constraints of Table Objectives.sql DDL
            cur.execute(
                """
                INSERT INTO objectives (
                    crucible_id,
                    objective_title,
                    objective_description,
                    objective_target_date,
                    objective_status
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (
                    args.crucible,
                    args.obj_title,
                    args.obj_desc,
                    args.obj_target,
                    args.obj_status
                )
            )
            conn.commit()
            print(f"\n[+] Created Objective #{cur.lastrowid}: {args.obj_title}")
        except sqlite3.IntegrityError as e:
            print(f"\n[!] Database Error: {e}")
            print("    Check if constraints were violated.", file=sys.stderr)
            sys.exit(1)

def modify_objective(args):
    updates = []
    params = []

    if args.obj_title:
        updates.append("objective_title = ?")
        params.append(args.obj_title)
    if args.obj_desc:
        updates.append("objective_description = ?")
        params.append(args.obj_desc)
    if args.obj_target:
        updates.append("objective_target_date = ?")
        params.append(args.obj_target)
    if args.obj_status:
        updates.append("objective_status = ?")
        params.append(args.obj_status)
    if args.crucible is not None:
        updates.append("crucible_id = ?")
        params.append(args.crucible)

    if not updates:
        print("\n[-] Error: No modifications provided. Provide at least one field to update.", file=sys.stderr)
        sys.exit(1)

    query = f"UPDATE objectives SET {', '.join(updates)} WHERE objective_id = ?"
    params.append(args.id)

    with get_db() as conn:
        cur = conn.cursor()
        cur.execute(query, tuple(params))
        if cur.rowcount == 0:
            print(f"\n[!] Error: Objective ID #{args.id} not found.", file=sys.stderr)
        else:
            conn.commit()
            print(f"\n[+] Successfully updated {cur.rowcount} column(s) for Objective #{args.id}.")

def delete_objective(args):
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM objectives WHERE objective_id = ?", (args.id,))
        
        if cur.rowcount == 0:
            print(f"\n[!] Error: Objective ID #{args.id} not found.", file=sys.stderr)
        else:
            conn.commit()
            print(f"\n[-] Objective #{args.id} permanently deleted.")

def add_session(args):
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
                pomo_complete
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                project_id,
                args.parent,
                args.priority,
                args.name if args.parent is None else None,
                args.plan,
                args.completed,
                args.interrupt,
                args.effort,
                args.energy,
                args.interrupt_type,
                args.friction,
                args.notes,
                1 if args.done else 0,
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

def modify_session(args):
    import sys
    updates = []
    params = []

    # Standard text/integer updates
    if args.name:
        updates.append("pomo_name = ?")
        params.append(args.name)
    if args.code:
        updates.append("project_id = (SELECT project_id FROM projects WHERE project_code = ?)")
        params.append(args.code.upper())
    if args.parent is not None:
        updates.append("pomo_id_parent = ?")
        params.append(args.parent)
    if args.notes:
        updates.append("notes = ?")
        params.append(args.notes)
    if args.done:
        updates.append("pomo_complete = 1")

    # Metrics & Telemetry: Only update if the flag was explicitly passed in the terminal
    if '--plan' in sys.argv:
        updates.append("poms_planned = ?")
        params.append(args.plan)
    if '--completed' in sys.argv:
        updates.append("poms_achieved = ?")
        params.append(args.completed)
    if '-i' in sys.argv or '--interrupt' in sys.argv:
        updates.append("poms_interrupted = ?")
        params.append(args.interrupt)
    if '-e' in sys.argv or '--effort' in sys.argv:
        updates.append("pomo_effort = ?")
        params.append(args.effort)
    if '--energy' in sys.argv:
        updates.append("pomo_energy = ?")
        params.append(args.energy)
    if '--friction' in sys.argv:
        updates.append("pomo_friction = ?")
        params.append(args.friction)
    if '--interrupt-type' in sys.argv:
        updates.append("pomo_interrupt_type = ?")
        params.append(args.interrupt_type)
    if '--priority' in sys.argv:
        updates.append("priority = ?")
        params.append(args.priority)

    if not updates:
        print("\n[-] Error: No modifications provided. Specify at least one field to update.", file=sys.stderr)
        sys.exit(1)

    query = f"UPDATE pomodoros SET {', '.join(updates)} WHERE pomo_id = ?"
    params.append(args.id)

    with get_db() as conn:
        cur = conn.cursor()
        cur.execute(query, tuple(params))
        if cur.rowcount == 0:
            print(f"\n[!] Error: Pomodoro ID #{args.id} not found.", file=sys.stderr)
        else:
            conn.commit()
            print(f"\n[+] Successfully updated {cur.rowcount} column(s) for Pomodoro #{args.id}.")

def delete_session(args):
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM pomodoros WHERE pomo_id = ?", (args.id,))
        
        if cur.rowcount == 0:
            print(f"\n[!] Error: Pomodoro ID #{args.id} not found.", file=sys.stderr)
        else:
            conn.commit()
            print(f"\n[-] Pomodoro #{args.id} permanently deleted.")

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

def add_project(args):
    with get_db() as conn:
        cur = conn.cursor()
        try:
            # Insert a new project mapping to the Table Projects.sql DDL
            cur.execute(
                """
                INSERT INTO projects (
                    project_code, 
                    project_name, 
                    objective_id, 
                    project_priority, 
                    project_status, 
                    weekly_pom_budget, 
                    project_contacts
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    args.code.upper(),
                    args.name,
                    args.objective,
                    args.proj_priority,
                    args.status,
                    args.budget,
                    args.contacts
                )
            )
            conn.commit()
            print(f"\n[+] Created Project: {args.code.upper()} -> {args.name}")
        except sqlite3.IntegrityError as e:
            print(f"\n[!] Database Error: {e}")
            print("    Check if the project_code already exists or constraints were violated.", file=sys.stderr)
            sys.exit(1)

def modify_project(args):
    # Dynamically build the SQL update statement based only on the arguments provided
    updates = []
    params = []

    if args.name:
        updates.append("project_name = ?")
        params.append(args.name)
    if args.objective is not None:
        updates.append("objective_id = ?")
        params.append(args.objective)
    if args.proj_priority:
        updates.append("project_priority = ?")
        params.append(args.proj_priority)
    if args.status:
        updates.append("project_status = ?")
        params.append(args.status)
    if args.budget is not None:
        updates.append("weekly_pom_budget = ?")
        params.append(args.budget)
    if args.contacts:
        updates.append("project_contacts = ?")
        params.append(args.contacts)

    if not updates:
        print("\n[-] Error: No modifications provided. Provide at least one field to update.", file=sys.stderr)
        sys.exit(1)

    # Append the WHERE clause identifier
    query = f"UPDATE projects SET {', '.join(updates)} WHERE project_code = ?"
    params.append(args.code.upper())

    with get_db() as conn:
        cur = conn.cursor()
        cur.execute(query, tuple(params))
        if cur.rowcount == 0:
            print(f"\n[!] Error: Project code '{args.code.upper()}' not found.", file=sys.stderr)
        else:
            conn.commit()
            print(f"\n[+] Successfully updated {cur.rowcount} column(s) for Project {args.code.upper()}.")

def delete_project(args):
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM projects WHERE project_code = ?", (args.code.upper(),))
        
        if cur.rowcount == 0:
            print(f"\n[!] Error: Project code '{args.code.upper()}' not found.", file=sys.stderr)
        else:
            conn.commit()
            print(f"\n[-] Project {args.code.upper()} permanently deleted.")

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

    # Objective Management Action Flags
    parser.add_argument("-o", "--objectives", action="store_true", help="List active objectives")
    parser.add_argument("--add-objective", action="store_true", help="Create a new objective")
    parser.add_argument("--edit-objective", action="store_true", help="Modify an existing objective")
    parser.add_argument("--delete-objective", action="store_true", help="Delete an objective")

    # Objective Metadata Arguments
    parser.add_argument("--obj-title", type=str, help="Title of the objective")
    parser.add_argument("--obj-desc", type=str, help="Description of the objective")
    parser.add_argument("--obj-target", type=str, help="Target date for the objective (YYYY-MM-DD)")
    parser.add_argument("--obj-status", type=str.upper, choices=['ACTIVE', 'COMPLETED', 'ON_HOLD', 'ARCHIVED'], default='ACTIVE', help="Objective lifecycle state (default: ACTIVE)")
    parser.add_argument("--crucible", type=int, default=None, help="Link to a crucible_id")

    # Session Management Action Flags
    parser.add_argument("--edit-session", action="store_true", help="Modify an existing pomodoro session")
    parser.add_argument("--delete-session", action="store_true", help="Delete a pomodoro session")
    parser.add_argument("--id", type=int, help="Target Pomodoro ID (required for edit/delete session)") 

    # Project Management Action Flags
    parser.add_argument("--add-project", action="store_true", help="Create a new project")
    parser.add_argument("--edit-project", action="store_true", help="Modify an existing project")
    parser.add_argument("--delete-project", action="store_true", help="Delete a project")

    # Project Metadata Arguments
    parser.add_argument("--objective", type=int, default=None, help="Link to an objective_id")
    parser.add_argument("--proj-priority", type=str.upper, choices=['DO', 'SCHEDULE', 'DELEGATE', 'DELETE'], default='SCHEDULE', help="Eisenhower matrix priority (default: SCHEDULE)")
    parser.add_argument("--status", type=str.upper, choices=['ACTIVE', 'PAUSED', 'COMPLETED'], default='ACTIVE', help="Project lifecycle state (default: ACTIVE)")
    parser.add_argument("--budget", type=int, default=0, help="Weekly pomodoro budget (default: 0)")
    parser.add_argument("--contacts", type=str, default=None, help="Associated project contacts or stakeholders")

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
    elif args.add_project:
        if not args.code or not args.name:
            print("[!] Error: --add-project requires both -c (code) and -n (name).")
            sys.exit(1)
        add_project(args)
    elif args.edit_project:
        if not args.code:
            print("[!] Error: --edit-project requires -c (code) to identify the project.")
            sys.exit(1)
        modify_project(args)
    elif args.delete_project:
        if not args.code:
            print("[!] Error: --delete-project requires -c (code) to identify the project.")
            sys.exit(1)
        delete_project(args)
    elif args.edit_session:
        if not args.id:
            print("[!] Error: --edit-session requires --id to identify the pomodoro.")
            sys.exit(1)
        modify_session(args)
    elif args.delete_session:
        if not args.id:
            print("[!] Error: --delete-session requires --id to identify the pomodoro.")
            sys.exit(1)
        delete_session(args)
    elif args.objectives:
        list_objectives()
    elif args.add_objective:
        if not args.obj_title:
            print("[!] Error: --add-objective requires --obj-title.")
            sys.exit(1)
        add_objective(args)
    elif args.edit_objective:
        if not args.id:
            print("[!] Error: --edit-objective requires --id to identify the objective.")
            sys.exit(1)
        modify_objective(args)
    elif args.delete_objective:
        if not args.id:
            print("[!] Error: --delete-objective requires --id to identify the objective.")
            sys.exit(1)
        delete_objective(args)
    elif args.code:
        add_session(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()