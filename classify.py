import fiftyone as fo
import anthropic, base64, json, os

client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

# Recreate dataset from images folder
dataset_name = "WasteWise_Demo"
if dataset_name in fo.list_datasets():
    fo.delete_dataset(dataset_name)

dataset = fo.Dataset.from_images_dir(
    "./waste_images",
    name=dataset_name,
    persistent=True
)
print(f"✅ Loaded {len(dataset)} images")

for sample in dataset:
    try:
        with open(sample.filepath, "rb") as f:
            img = base64.b64encode(f.read()).decode()
        ext = sample.filepath.split(".")[-1].lower()
        mt = "image/jpeg" if ext in ["jpg","jpeg"] else "image/png"

        r = client.messages.create(
            model="claude-sonnet-4-6", max_tokens=200,
            system='Respond ONLY in JSON no markdown: {"item":"name","bin":"recycling or landfill or compost or special","confidence":0.0}',
            messages=[{"role":"user","content":[
                {"type":"image","source":{"type":"base64","media_type":mt,"data":img}},
                {"type":"text","text":"Classify this waste for Tempe AZ"}
            ]}]
        )
        text = r.content[0].text.strip()
        start = text.find("{")
        end = text.rfind("}") + 1
        result = json.loads(text[start:end])

        sample["bin_type"]   = result["bin"]
        sample["waste_item"] = result["item"]
        sample["confidence"] = result["confidence"]
        sample.save()
        print(f"✅ {result['item']} → {result['bin']} ({result['confidence']:.0%})")

    except Exception as e:
        print(f"❌ Skipped: {e}")

print("\n✅ Done! Opening FiftyOne...")
session = fo.launch_app(dataset)
input("Press Enter to quit")
