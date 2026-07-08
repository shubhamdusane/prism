"""
Prism - Core Example
Demonstrates basic Prism functionality for multi-modal agent input/output processing.
"""

from prism import Prism, Input, Output, Processor

def main():
    # Initialize Prism
    prism = Prism(name="multi-modal-processor")

    # Create input sources
    text_input = Input(type="text", source="user_query")
    image_input = Input(type="image", source="camera_feed")

    # Create output targets
    text_output = Output(type="text", target="display")
    audio_output = Output(type="audio", target="speaker")

    # Register processors
    processor = Processor(
        name="vision-processor",
        inputs=[text_input, image_input],
        outputs=[text_output, audio_output]
    )
    prism.register(processor)

    # Process multi-modal input
    result = prism.process(
        text="Describe this image",
        image="snapshot.jpg"
    )

    print(f"Prism: {prism.name}")
    print(f"Registered processors: {prism.processor_count}")
    print(f"Processing result: {result.status}")

if __name__ == "__main__":
    main()
