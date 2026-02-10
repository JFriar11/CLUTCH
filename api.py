"""
Flask API for MLB Clutch Factor Analyzer
Run with: python api.py
"""
from flask import Flask, jsonify, request
from flask_cors import CORS
import pandas as pd
import traceback

from src.config import DEFAULT_START_DATE, DEFAULT_END_DATE, MIN_HIGH_LEV_PA, MIN_ALL_PA
from src.data_pull import pull_statcast_pa
from src.features import prepare_pa_frame
from src.metrics import woba, ops, k_pct
from src.clutch_score import compute_clutch_factor

app = Flask(__name__)
CORS(app)  # Allow requests from your HTML file

@app.route('/api/health', methods=['GET'])
def health_check():
    """Simple health check endpoint"""
    return jsonify({
        'status': 'ok',
        'message': 'MLB Clutch Factor API is running'
    })

@app.route('/api/analyze', methods=['POST'])
def analyze():
    """
    Main analysis endpoint
    Expected JSON body:
    {
        "start_date": "2024-03-28",
        "end_date": "2024-09-29",
        "min_all_pa": 250,
        "min_high_pa": 50,
        "chunk_days": 7
    }
    """
    try:
        # Get parameters from request
        data = request.json
        start_date = data.get('start_date', DEFAULT_START_DATE)
        end_date = data.get('end_date', DEFAULT_END_DATE)
        min_all_pa = data.get('min_all_pa', MIN_ALL_PA)
        min_high_pa = data.get('min_high_pa', MIN_HIGH_LEV_PA)
        chunk_days = data.get('chunk_days', 7)

        print(f"\n{'='*60}")
        print(f"Starting analysis: {start_date} to {end_date}")
        print(f"Min PA: {min_all_pa} (all), {min_high_pa} (high leverage)")
        print(f"{'='*60}\n")

        # Step 1: Pull Statcast data
        print("Step 1: Pulling Statcast data...")
        raw_data = pull_statcast_pa(start_date, end_date, chunk_days=chunk_days)
        
        if raw_data.empty:
            return jsonify({
                'success': False,
                'error': 'No data returned from Statcast. Check your date range.',
                'data': []
            }), 400

        print(f"  ✓ Pulled {len(raw_data)} rows")

        # Step 2: Prepare PA frame
        print("Step 2: Preparing plate appearance data...")
        df = prepare_pa_frame(raw_data)
        
        if df.empty:
            return jsonify({
                'success': False,
                'error': 'No valid plate appearances found after processing.',
                'data': []
            }), 400

        print(f"  ✓ Processed {len(df)} plate appearances")
        print(f"  ✓ Found {df['batter_name'].nunique()} unique batters")

        # Step 3: Split into all vs high leverage
        all_pa = df.copy()
        high_pa = df[df["is_high_lev"]].copy()

        print(f"  ✓ High leverage PAs: {len(high_pa)} ({len(high_pa)/len(df)*100:.1f}%)")

        # Step 4: Compute metrics
        print("Step 3: Computing metrics...")
        pa_all = all_pa.groupby("batter_name").size()
        pa_high = high_pa.groupby("batter_name").size()

        woba_all = woba(all_pa)
        woba_high = woba(high_pa)

        ops_all = ops(all_pa)
        ops_high = ops(high_pa)

        k_all = k_pct(all_pa)
        k_high = k_pct(high_pa)

        # Step 5: Compute ClutchFactor
        print("Step 4: Computing ClutchFactor...")
        clutch = compute_clutch_factor(woba_all, woba_high, ops_all, ops_high, k_all, k_high)

        # Step 6: Build output dataframe
        out = pd.DataFrame({
            "PA_all": pa_all,
            "PA_high": pa_high,
            "wOBA_all": woba_all,
            "wOBA_high": woba_high,
            "OPS_all": ops_all,
            "OPS_high": ops_high,
            "K%_all": k_all,
            "K%_high": k_high,
            "ClutchFactor": clutch,
            "LI_used_in_flag": df["li_used"].iloc[0] if "li_used" in df.columns and len(df) > 0 else False
        }).fillna(0.0)

        # Step 7: Apply filters
        print("Step 5: Applying filters...")
        before_filter = len(out)
        out = out[(out["PA_high"] >= min_high_pa) & (out["PA_all"] >= min_all_pa)]
        print(f"  ✓ {len(out)} players after filtering (removed {before_filter - len(out)})")

        # Step 8: Sort by ClutchFactor
        out = out.sort_values("ClutchFactor", ascending=False)

        # Step 9: Convert to JSON-friendly format
        # Reset index so batter_name becomes a column
        out = out.reset_index()
        
        # Convert to list of dictionaries
        results = out.to_dict('records')

        print(f"\n{'='*60}")
        print(f"✓ Analysis complete! Returning {len(results)} players")
        print(f"{'='*60}\n")

        # Show top 5 in console
        print("Top 5 Clutch Performers:")
        for i, player in enumerate(results[:5], 1):
            print(f"  {i}. {player['batter_name']}: {player['ClutchFactor']:.2f}")

        return jsonify({
            'success': True,
            'data': results,
            'metadata': {
                'start_date': start_date,
                'end_date': end_date,
                'total_players': len(results),
                'min_all_pa': min_all_pa,
                'min_high_pa': min_high_pa,
                'li_used': bool(out['LI_used_in_flag'].iloc[0]) if len(out) > 0 else False
            }
        })

    except Exception as e:
        print(f"\n{'!'*60}")
        print(f"ERROR: {str(e)}")
        print(f"{'!'*60}\n")
        traceback.print_exc()
        
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc(),
            'data': []
        }), 500

if __name__ == '__main__':
    print("\n" + "="*60)
    print("MLB CLUTCH FACTOR API SERVER")
    print("="*60)
    print("Server starting on http://localhost:5000")
    print("Endpoints:")
    print("  GET  /api/health   - Health check")
    print("  POST /api/analyze  - Run clutch analysis")
    print("="*60 + "\n")
    
    app.run(debug=True, port=5001, host='0.0.0.0')