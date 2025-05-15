# Supabase Log Exporter

This tool exports logs from Supabase tables to local files in both JSON and text formats.

## Setup

1. Make sure your `.env` file contains the Supabase URL and key:
   ```
   SUPABASE_URL="your-supabase-url"
   SUPABASE_KEY="your-supabase-key"
   ```

2. Install required packages:
   ```
   pip install supabase python-dotenv
   ```

## Usage

### Basic Usage

Run the script to export logs from the default tables (agent_logs, chatbot_logs, summarizer_logs):

```bash
python export_logs.py
```

This will:
- Create a `logs` directory if it doesn't exist
- Export logs from each table to both JSON and text files
- Save the files in the `logs` directory

### Advanced Usage

You can customize the export with command-line arguments:

```bash
python export_logs.py --tables agent_logs chatbot_logs --days 7 --limit 500 --debug
```

Arguments:
- `--tables`: Specify which tables to export (space-separated)
- `--days`: Number of days of logs to fetch (default: 30)
- `--limit`: Maximum number of logs to fetch per table (default: 1000)
- `--debug`: Enable debug output with more details

## Output Files

For each table, two files are created:
1. `logs/{table_name}.json` - Contains the raw JSON data
2. `logs/{table_name}.txt` - Contains a human-readable formatted version

## Troubleshooting

If you encounter errors:

1. **"supabase_url is required"**: Check that your `.env` file has the correct format without spaces around the equals sign:
   ```
   SUPABASE_URL="https://your-project.supabase.co"
   SUPABASE_KEY="your-key"
   ```

2. **"column does not exist"**: The script will try to auto-detect timestamp fields, but if it fails, you may need to modify the script to match your table structure.

3. **No data retrieved**: Check that the tables exist in your Supabase project and contain data.

## Alternative Simple Script

If you prefer a simpler approach, you can also use `fetch_logs.py` which has fewer options but is easier to modify for specific needs.

```bash
python fetch_logs.py
```
