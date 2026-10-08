import argparse
from generate_synthetic_data import generate_transactions
from src.pipeline.orchestrator import run_pipeline
from src.reporting.generator import generate_report

def main():
    parser = argparse.ArgumentParser(description="BudgetWise Pipeline")
    parser.add_argument('--generate', action='store_true', help='Generate synthetic data')
    parser.add_argument('--pipeline', action='store_true', help='Run ML pipeline')
    parser.add_argument('--report', action='store_true', help='Generate HTML report')
    parser.add_argument('--all', action='store_true', help='Run everything')
    
    args = parser.parse_args()
    
    if args.all or args.generate:
        generate_transactions()
        
    forecast = None
    if args.all or args.pipeline:
        forecast = run_pipeline()
        
    if args.all or args.report:
        generate_report(forecast)
        
    if not any([args.generate, args.pipeline, args.report, args.all]):
        print("Please specify an action. Run with --help for options. Example: python main.py --all")

if __name__ == "__main__":
    main()
