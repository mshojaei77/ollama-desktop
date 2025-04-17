#!/usr/bin/env python3
import ollama

def main():
    # Specify the model and payload
    response = ollama.chat(
        model="granite3.2-vision",
        messages=[
            {
                "role": "user",
                "content": "do an ocr and write ant text in this image",
                # You can pass file paths directly
                "images": ["sample.png"]
            }
        ]
    )

    # Print out the model's reply
    print(response["message"]["content"])

if __name__ == "__main__":
    main()