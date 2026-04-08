import json
import pandas as pd

print("="*70)
print("COMPARISON OF MODELS")
print("="*70)

results_files = ['results_xgboost.json', 'results_lightgbm.json', 'results_catboost.json', 'results_mlp.json']

all_results = []
for f in results_files:
    try:
        with open(f, 'r') as file:
            data = json.load(file)
            all_results.append(data)
    except FileNotFoundError:
        print(f"File {f} not found")

df = pd.DataFrame(all_results)
df = df.sort_values('cfo_accuracy', ascending=False)

print("\n" + "="*70)
print("RESULTS SUMMARY")
print("="*70)
print(df.to_string(index=False))

print("\n" + "="*70)
print("BEST MODEL BY CFO ACCURACY")
print("="*70)
best = df.iloc[0]
print(f"Model: {best['model']}")
print(f"CFO Accuracy: {best['cfo_accuracy']:.4f}")
print(f"PL Accuracy: {best['pl_accuracy']:.4f}")
print(f"Total Time: {best['pl_time'] + best['cfo_time']:.1f}s")

df.to_csv('comparison_results.csv', index=False)
print("\nSaved: comparison_results.csv")
