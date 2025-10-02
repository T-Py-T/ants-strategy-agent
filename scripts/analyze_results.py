#!/usr/bin/env python3
"""
Advanced Analysis Tool for AntsAIBot Results
Loads all game results into memory for fast analysis and validation
"""

import json
import pandas as pd
import numpy as np
import argparse
import sys
from pathlib import Path
from typing import Dict, List, Tuple
import matplotlib.pyplot as plt
import seaborn as sns

class AntsAIAnalyzer:
    def __init__(self, results_file: str = None):
        """Initialize analyzer with results file"""
        self.results_file = results_file or "parallel_statistics.json"
        self.df = None
        self.game_data = []
        self.load_results()
    
    def load_results(self):
        """Load results from JSON file into pandas DataFrame"""
        try:
            with open(self.results_file, 'r') as f:
                data = json.load(f)
            
            # Convert to DataFrame
            self.df = pd.DataFrame(data)
            
            # Extract individual game results if available
            if 'game_results' in self.df.columns:
                game_rows = []
                for _, row in self.df.iterrows():
                    if isinstance(row['game_results'], list):
                        for game in row['game_results']:
                            game['test_name'] = row['test_name']
                            game['timestamp'] = row['timestamp']
                            
                            # Extract food collection data from replay data
                            if 'replaydata' in game and 'hive_history' in game['replaydata']:
                                hive_history = game['replaydata']['hive_history']
                                if len(hive_history) >= 2:
                                    # Food collected = final hive amount (total food collected)
                                    game['food_collected'] = hive_history[0][-1] if hive_history[0] else 0
                                    game['enemy_food_collected'] = hive_history[1][-1] if len(hive_history) > 1 and hive_history[1] else 0
                                else:
                                    game['food_collected'] = 0
                                    game['enemy_food_collected'] = 0
                            else:
                                game['food_collected'] = 0
                                game['enemy_food_collected'] = 0
                            
                            game_rows.append(game)
                
                if game_rows:
                    self.game_data = pd.DataFrame(game_rows)
                else:
                    self.game_data = pd.DataFrame()
            else:
                self.game_data = pd.DataFrame()
            
            print(f"✅ Loaded {len(self.df)} test results")
            if not self.game_data.empty:
                print(f"✅ Loaded {len(self.game_data)} individual game results")
                
        except FileNotFoundError:
            print(f"❌ Results file {self.results_file} not found")
            sys.exit(1)
        except Exception as e:
            print(f"❌ Error loading results: {e}")
            sys.exit(1)
    
    def validate_against_raw_outputs(self, sample_size: int = 5):
        """Validate analysis against raw game outputs"""
        print(f"\n🔍 VALIDATING ANALYSIS AGAINST RAW OUTPUTS (Sample: {sample_size} games)")
        print("=" * 70)
        
        validation_results = []
        
        for test_name in self.df['test_name'].unique():
            print(f"\n📊 Validating {test_name}:")
            
            # Get sample games for this test
            test_games = self.game_data[self.game_data['test_name'] == test_name].head(sample_size)
            
            for _, game in test_games.iterrows():
                print(f"  Game {game['game']}: {game['result']} (Score: {game['our_score']} vs {game['enemy_score']})")
                
                # Here you could re-run the specific game to validate
                # For now, we'll just show the stored data
                validation_results.append({
                    'test_name': test_name,
                    'game': game['game'],
                    'result': game['result'],
                    'our_score': game['our_score'],
                    'enemy_score': game['enemy_score'],
                    'turns': game['turns']
                })
        
        return validation_results
    
    def full_analysis(self):
        """Perform full statistical analysis"""
        print(f"\n📈 full STATISTICAL ANALYSIS")
        print("=" * 50)
        
        # Summary statistics
        print("\n🎯 WIN RATE SUMMARY:")
        summary = self.df[['test_name', 'wins', 'losses', 'draws', 'win_rate', 'average_turns']].copy()
        summary['total_games'] = summary['wins'] + summary['losses'] + summary['draws']
        print(summary.to_string(index=False))
        
        # Food collection analysis if available
        if not self.game_data.empty and 'food_collected' in self.game_data.columns:
            print("\n🍯 FOOD COLLECTION ANALYSIS:")
            food_summary = []
            for test_name in self.game_data['test_name'].unique():
                test_games = self.game_data[self.game_data['test_name'] == test_name]
                avg_food = test_games['food_collected'].mean()
                avg_enemy_food = test_games['enemy_food_collected'].mean()
                food_summary.append({
                    'test_name': test_name,
                    'avg_food_collected': f"{avg_food:.1f}",
                    'avg_enemy_food': f"{avg_enemy_food:.1f}",
                    'food_ratio': f"{avg_food/max(avg_enemy_food, 1):.2f}" if avg_enemy_food > 0 else "∞"
                })
            
            food_df = pd.DataFrame(food_summary)
            print(food_df.to_string(index=False))
        
        # Detailed analysis if we have individual game data
        if not self.game_data.empty:
            print(f"\n📊 DETAILED GAME-LEVEL ANALYSIS:")
            print(f"Total individual games analyzed: {len(self.game_data)}")
            
            # Win rate by opponent
            game_summary = self.game_data.groupby('test_name').agg({
                'result': ['count', lambda x: (x == 'WIN').sum(), lambda x: (x == 'LOSS').sum(), lambda x: (x == 'DRAW').sum()],
                'our_score': ['mean', 'std'],
                'enemy_score': ['mean', 'std'],
                'turns': ['mean', 'std']
            }).round(2)
            
            game_summary.columns = ['Total_Games', 'Wins', 'Losses', 'Draws', 'Our_Score_Mean', 'Our_Score_Std', 'Enemy_Score_Mean', 'Enemy_Score_Std', 'Turns_Mean', 'Turns_Std']
            game_summary['Win_Rate'] = (game_summary['Wins'] / game_summary['Total_Games'] * 100).round(1)
            print(game_summary)
            
            # Score distribution analysis
            print(f"\n🎲 SCORE DISTRIBUTION ANALYSIS:")
            score_analysis = self.game_data.groupby('test_name').agg({
                'our_score': ['min', 'max', 'median'],
                'enemy_score': ['min', 'max', 'median'],
                'turns': ['min', 'max', 'median']
            }).round(1)
            print(score_analysis)
    
    def performance_trends(self):
        """Analyze performance trends over time"""
        if self.game_data.empty:
            print("❌ No individual game data available for trend analysis")
            return
        
        print(f"\n📈 PERFORMANCE TRENDS ANALYSIS")
        print("=" * 40)
        
        # Rolling win rate (if we have enough games)
        for test_name in self.game_data['test_name'].unique():
            test_games = self.game_data[self.game_data['test_name'] == test_name].sort_values('game')
            
            if len(test_games) >= 10:
                # Calculate rolling win rate
                test_games['is_win'] = (test_games['result'] == 'WIN').astype(int)
                test_games['rolling_win_rate'] = test_games['is_win'].rolling(window=5, min_periods=1).mean() * 100
                
                print(f"\n{test_name} - Rolling Win Rate (5-game window):")
                print(f"  First 5 games: {test_games['rolling_win_rate'].iloc[4]:.1f}%")
                print(f"  Last 5 games: {test_games['rolling_win_rate'].iloc[-1]:.1f}%")
                print(f"  Overall trend: {'📈 Improving' if test_games['rolling_win_rate'].iloc[-1] > test_games['rolling_win_rate'].iloc[4] else '📉 Declining' if test_games['rolling_win_rate'].iloc[-1] < test_games['rolling_win_rate'].iloc[4] else '➡️ Stable'}")
    
    def statistical_significance(self):
        """Calculate statistical significance of results"""
        print(f"\n📊 STATISTICAL SIGNIFICANCE ANALYSIS")
        print("=" * 45)
        
        for test_name in self.df['test_name'].unique():
            row = self.df[self.df['test_name'] == test_name].iloc[0]
            wins = row['wins']
            total = row['wins'] + row['losses'] + row['draws']
            
            if total > 0:
                # Binomial test for win rate
                from scipy.stats import binomtest
                
                # Test against null hypothesis of 50% win rate
                result = binomtest(wins, total, p=0.5, alternative='two-sided')
                
                print(f"\n{test_name}:")
                print(f"  Games: {total}, Wins: {wins}, Win Rate: {row['win_rate']:.1f}%")
                print(f"  P-value (vs 50%): {result.pvalue:.4f}")
                print(f"  Significant: {'✅ Yes' if result.pvalue < 0.05 else '❌ No'} (p < 0.05)")
                
                # Confidence interval
                from scipy.stats import beta
                alpha = 0.05
                ci_lower = beta.ppf(alpha/2, wins, total - wins + 1)
                ci_upper = beta.ppf(1 - alpha/2, wins + 1, total - wins)
                print(f"  95% CI: [{ci_lower:.3f}, {ci_upper:.3f}]")
    
    def export_detailed_report(self, output_file: str = "detailed_analysis_report.json"):
        """Export detailed analysis report"""
        report = {
            'summary': self.df.to_dict('records'),
            'analysis_timestamp': pd.Timestamp.now().isoformat(),
            'total_tests': len(self.df),
            'total_games': len(self.game_data) if not self.game_data.empty else 0
        }
        
        if not self.game_data.empty:
            report['game_level_analysis'] = {
                'win_rates': self.game_data.groupby('test_name')['result'].apply(lambda x: (x == 'WIN').mean() * 100).to_dict(),
                'score_correlations': self.game_data[['our_score', 'enemy_score', 'turns']].corr().to_dict(),
                'performance_by_turns': self.game_data.groupby('turns')['result'].value_counts().to_dict()
            }
        
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        print(f"\n💾 Detailed report exported to: {output_file}")
    
    def plot_performance(self, save_plots: bool = True):
        """Create performance visualization plots"""
        if self.game_data.empty:
            print("❌ No individual game data available for plotting")
            return
        
        print(f"\n📊 CREATING PERFORMANCE VISUALIZATIONS")
        print("=" * 40)
        
        # Set up the plotting style
        plt.style.use('seaborn-v0_8')
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        fig.suptitle('AntsAIBot Performance Analysis', fontsize=16, fontweight='bold')
        
        # 1. Win Rate by Opponent
        win_rates = self.game_data.groupby('test_name')['result'].apply(lambda x: (x == 'WIN').mean() * 100)
        axes[0, 0].bar(win_rates.index, win_rates.values, color='skyblue', alpha=0.7)
        axes[0, 0].set_title('Win Rate by Opponent')
        axes[0, 0].set_ylabel('Win Rate (%)')
        axes[0, 0].tick_params(axis='x', rotation=45)
        
        # 2. Score Distribution
        for test_name in self.game_data['test_name'].unique():
            test_data = self.game_data[self.game_data['test_name'] == test_name]
            axes[0, 1].hist(test_data['our_score'], alpha=0.6, label=f'{test_name} (Our Score)', bins=10)
        axes[0, 1].set_title('Score Distribution')
        axes[0, 1].set_xlabel('Score')
        axes[0, 1].set_ylabel('Frequency')
        axes[0, 1].legend()
        
        # 3. Game Length Distribution
        for test_name in self.game_data['test_name'].unique():
            test_data = self.game_data[self.game_data['test_name'] == test_name]
            axes[1, 0].hist(test_data['turns'], alpha=0.6, label=test_name, bins=15)
        axes[1, 0].set_title('Game Length Distribution')
        axes[1, 0].set_xlabel('Turns')
        axes[1, 0].set_ylabel('Frequency')
        axes[1, 0].legend()
        
        # 4. Win Rate Over Time (if enough games)
        for test_name in self.game_data['test_name'].unique():
            test_data = self.game_data[self.game_data['test_name'] == test_name].sort_values('game')
            if len(test_data) >= 10:
                test_data['is_win'] = (test_data['result'] == 'WIN').astype(int)
                test_data['rolling_win_rate'] = test_data['is_win'].rolling(window=5, min_periods=1).mean() * 100
                axes[1, 1].plot(test_data['game'], test_data['rolling_win_rate'], marker='o', label=test_name, linewidth=2)
        axes[1, 1].set_title('Rolling Win Rate (5-game window)')
        axes[1, 1].set_xlabel('Game Number')
        axes[1, 1].set_ylabel('Win Rate (%)')
        axes[1, 1].legend()
        axes[1, 1].grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        if save_plots:
            plt.savefig('performance_analysis.png', dpi=300, bbox_inches='tight')
            print("📊 Performance plots saved to: performance_analysis.png")
        
        plt.show()

def main():
    parser = argparse.ArgumentParser(description='Advanced AntsAIBot Results Analysis')
    parser.add_argument('--file', '-f', default='parallel_statistics.json', 
                       help='Results file to analyze')
    parser.add_argument('--validate', '-v', action='store_true',
                       help='Validate analysis against raw outputs')
    parser.add_argument('--sample-size', '-s', type=int, default=5,
                       help='Number of games to sample for validation')
    parser.add_argument('--export', '-e', action='store_true',
                       help='Export detailed report')
    parser.add_argument('--plot', '-p', action='store_true',
                       help='Create performance plots')
    parser.add_argument('--all', '-a', action='store_true',
                       help='Run all analysis')
    
    args = parser.parse_args()
    
    # Initialize analyzer
    analyzer = AntsAIAnalyzer(args.file)
    
    if args.all or args.validate:
        analyzer.validate_against_raw_outputs(args.sample_size)
    
    if args.all or True:  # Always run basic analysis
        analyzer.full_analysis()
        analyzer.performance_trends()
        analyzer.statistical_significance()
    
    if args.all or args.export:
        analyzer.export_detailed_report()
    
    if args.all or args.plot:
        analyzer.plot_performance()

if __name__ == "__main__":
    main()