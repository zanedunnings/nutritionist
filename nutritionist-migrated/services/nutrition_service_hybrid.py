
        Assistant: Please provide a structured nutrition summary based on the food analysis data.

        Human: """

        # Use Anthropic 0.7.7 API (legacy completion format)
        response = client.completions.create(
            model="claude-v1",
            prompt=prompt,
            max_tokens_to_sample=1000,
            temperature=0.3
        )
        
        # Handle response format for anthropic 0.7.7
        completion_text = response.completion if hasattr(response, 'completion') else str(response)
        
        return {
            "success": True,
            "summary": completion_text,
            "model": "claude-v1"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "model": "claude-v1"
        }

def analyze_food_image(image_path: str) -> Dict[str, Any]:
    """
    Main function: Analyze food image using LogMeal API + Anthropic text processing
    """
    try:
        # Step 1: Analyze image with LogMeal API
        food_analysis = analyze_food_image_logmeal(image_path)
        
        if not food_analysis["success"]:
            return food_analysis
        
        # Step 2: Generate nutrition summary with Anthropic
        nutrition_summary = generate_nutrition_summary(food_analysis["analysis"])
        
        # Combine results
        return {
            "success": True,
            "raw_analysis": food_analysis["analysis"],
            "nutrition_summary": nutrition_summary.get("summary", ""),
            "models_used": {
                "vision": food_analysis["model"],
                "text_processing": nutrition_summary.get("model", "")
            }
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "models_used": {
                "vision": "logmeal-api",
                "text_processing": "claude-v1"
            }
        }
