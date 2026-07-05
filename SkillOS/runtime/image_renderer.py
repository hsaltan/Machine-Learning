
from typing import Any
from pathlib import Path

import torch
from diffusers import FluxPipeline
from IPython.display import display


def generate_images(
    command: dict[str, Any],
    hf_token: str,
) -> list[str]:
    """
    Generate images from a structured runtime command.

    Description
    -----------
    Uses the FLUX image generation model to create one or more images
    from the supplied prompt, saves them to disk, displays each image
    in the notebook, and returns the saved file paths.

    Args
    ----
    command:
        Dictionary containing the image generation parameters.

        Expected fields include:

        - prompt
        - num_images
        - width
        - height
        - image_format
        - output_folder
        - filename_prefix
        - seed

    hf_token:
        Hugging Face access token used to download the FLUX model.

    Returns
    -------
    list[str]

        Paths of the generated image files.

    Raises
    ------
    RuntimeError

        If image generation fails.

    Example
    -------
    >>> generate_images(
    ...     command,
    ...     hf_token,
    ... )
    """

    # -----------------------------------------------------
    # Read command parameters
    # -----------------------------------------------------

    prompt = command["prompt"]
    num_images = command.get("num_images", 1)
    width = command.get("width", 512)
    height = command.get("height", 512)
    image_format = command.get("image_format", "png")
    output_folder = Path(
        command.get(
            "output_folder",
            "/kaggle/working/images",
        )
    )
    filename_prefix = command.get(
        "filename_prefix",
        "image",
    )
    seed = command.get("seed", 42)

    # -----------------------------------------------------
    # Create output directory
    # -----------------------------------------------------

    output_folder.mkdir(
        parents=True,
        exist_ok=True,
    )

    # -----------------------------------------------------
    # Select device and tensor precision
    # -----------------------------------------------------

    device = (
        "cuda"
        if torch.cuda.is_available()
        else "cpu"
    )

    dtype = (
        torch.bfloat16
        if device == "cuda"
        else torch.float32
    )

    # -----------------------------------------------------
    # Load the FLUX image generation pipeline
    # -----------------------------------------------------

    pipe = FluxPipeline.from_pretrained(
        "black-forest-labs/FLUX.1-schnell",
        torch_dtype=dtype,
        token=hf_token,
    ).to(device)

    # pipe.enable_model_cpu_offload()
    pipe.enable_attention_slicing()
    pipe.enable_vae_slicing()
    pipe.enable_vae_tiling()

    # -----------------------------------------------------
    # Create reproducible random generator (optional)
    # -----------------------------------------------------

    generator = None

    if seed is not None:
        generator = (
            torch.Generator(device=device)
            .manual_seed(seed)
        )

    # -----------------------------------------------------
    # Generate images
    # -----------------------------------------------------

    saved_files: list[str] = []

    for index in range(num_images):

        image = pipe(
            prompt=prompt,
            width=width,
            height=height,
            guidance_scale=0.0,
            num_inference_steps=4,
            generator=generator,
        ).images[0]

        file_path = output_folder / (
            f"{filename_prefix}_{index + 1}.{image_format}"
        )

        image.save(file_path)

        display(image)

        saved_files.append(
            str(file_path)
        )

    # -----------------------------------------------------
    # Return generated file paths
    # -----------------------------------------------------

    return saved_files
