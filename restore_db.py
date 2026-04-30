import psycopg2
import sys
import os
import io

# Database connection details
DB_PARAMS = {
    "host": "aws-1-ap-southeast-2.pooler.supabase.com",
    "port": 5432,
    "database": "postgres",
    "user": "postgres.hdsntducurmhossannue",
    "password": "Wallposter27@"
}
BACKUP_FILE = r"d:\sentimatix\backup\db_cluster-05-12-2025@19-21-16.backup\db_cluster-05-12-2025@19-21-16.backup"

def restore():
    print(f"Connecting to database...", flush=True)
    try:
        conn = psycopg2.connect(**DB_PARAMS)
        conn.autocommit = True
        cur = conn.cursor()
        print("Connected successfully.", flush=True)
    except Exception as e:
        print(f"Error connecting to database: {e}", flush=True)
        return

    print(f"Reading backup file: {BACKUP_FILE}", flush=True)
    if not os.path.exists(BACKUP_FILE):
        print(f"File not found: {BACKUP_FILE}", flush=True)
        return

    with open(BACKUP_FILE, 'r', encoding='utf-8') as f:
        statement = ""
        copy_mode = False
        copy_command = ""
        copy_data = []
        
        count = 0
        success = 0
        failed = 0
        error_count = 0
        
        for line in f:
            if copy_mode:
                if line.strip() == '\\.':
                    print(f"\nExecuting COPY for {copy_command.split()[1]}...", flush=True)
                    try:
                        data_io = io.StringIO("".join(copy_data))
                        cur.copy_expert(copy_command, data_io)
                        success += 1
                        print(f"COPY successful.", flush=True)
                    except Exception as e:
                        failed += 1
                        if error_count < 10:
                            print(f"COPY failed: {e}", flush=True)
                            error_count += 1
                        pass
                    copy_mode = False
                    copy_data = []
                    copy_command = ""
                else:
                    copy_data.append(line)
                continue

            if line.strip().startswith('\\'):
                continue
                
            if line.strip().startswith('COPY') and 'FROM stdin;' in line:
                copy_mode = True
                copy_command = line.strip()
                continue

            if any(x in line for x in ['CREATE ROLE', 'ALTER ROLE', 'GRANT']):
                if 'GRANT ALL ON SCHEMA public' not in line:
                    continue

            statement += line
            if ';' in line:
                cmd = statement.strip()
                if cmd:
                    count += 1
                    try:
                        cur.execute(cmd)
                        success += 1
                    except Exception as e:
                        failed += 1
                        if error_count < 10:
                            print(f"\nError in statement {count}: {e}", flush=True)
                            print(f"Statement was: {cmd[:200]}...", flush=True)
                            error_count += 1
                        pass
                statement = ""
            
            if count % 100 == 0 and count > 0 and statement == "":
                print(f"Processed {count} statements... (Success: {success}, Failed: {failed})", flush=True)

    print(f"\nRestoration completed. Total ops: {count + success + failed}, Success: {success}, Failed: {failed}", flush=True)
    cur.close()
    conn.close()

if __name__ == "__main__":
    restore()
