import dspy
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# --------------------------------
# CONFIGURE OLLAMA ENDPOINT
# --------------------------------
os.environ["OLLAMA_HOST"] = "http://localhost:11434"

lm = dspy.LM(
    model="ollama/gpt-oss:latest",
    api_base="http://localhost:11434",
)

dspy.configure(lm=lm)

# --------------------------------
# DSPy SIGNATURE + MODULE
# --------------------------------
class StockPredict(dspy.Signature):
    symbol = dspy.InputField()
    direction = dspy.OutputField(desc="Predict 'up' or 'down'")

class StockPredictModule(dspy.Module):
    def __init__(self):
        super().__init__()
        self.predict = dspy.Predict(StockPredict)

    def forward(self, symbol):
        return self.predict(symbol=symbol)

# --------------------------------
# CUSTOM METRIC FUNCTION
# --------------------------------
def exact_match_metric(example, pred, trace=None):
    return pred.direction.lower() == example.direction.lower()

predictor = StockPredictModule()

# --------------------------------
# TRAINING EXAMPLES
# --------------------------------
train_examples = [
    dspy.Example(symbol="AAPL", direction="down").with_inputs("symbol"),
    dspy.Example(symbol="GOOGL", direction="up").with_inputs("symbol"),
    dspy.Example(symbol="TSLA", direction="up").with_inputs("symbol"),
    dspy.Example(symbol="MSFT", direction="up").with_inputs("symbol"),
]

# --------------------------------
# OPTIMIZATION USING BOOTSTRAP FEW-SHOT
# --------------------------------
optimizer = dspy.BootstrapFewShot(
    metric=exact_match_metric,
    max_bootstrapped_demos=3,
    max_labeled_demos=4,
    max_rounds=1
)

# Compile the optimized predictor
optimized_predictor = optimizer.compile(predictor, trainset=train_examples)

# --------------------------------
# OPTIMIZATION SUMMARY TABLE
# --------------------------------
print("\n=== Optimization Summary ===")
print(f"{'Symbol':<10}{'Predicted':<10}{'Actual':<10}{'Match':<6}")
print("-" * 36)

for ex in train_examples:
    pred_obj = optimized_predictor(ex.symbol)
    match = pred_obj.direction.lower() == ex.direction.lower()
    print(f"{ex.symbol:<10}{pred_obj.direction:<10}{ex.direction:<10}{str(match):<6}")

# --------------------------------
# TEST THE MODEL
# --------------------------------
test_symbol = "INFY"
pred = optimized_predictor(test_symbol)
print("\nPrediction for", test_symbol, ":", pred.direction)

# Save the optimized predictor
optimized_predictor.save(os.path.join(BASE_DIR, "stock_predictor.json"))
print("\nSaved optimized predictor to 'stock_predictor.json'")
print("   Open this file to see the exact prompts and demos!")