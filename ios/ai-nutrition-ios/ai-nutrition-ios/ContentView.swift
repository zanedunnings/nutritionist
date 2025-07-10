//
//  ContentView.swift
//  ai-nutrition-ios
//
//  Created by Zane Dunnings on 7/9/25.
//

import SwiftUI
import PhotosUI

struct ContentView: View {
    // Sample data - in a real app, this would come from your data model
    @State private var caloriesSavedThisWeek: Int = 2450
    @State private var caloriesLeftToday: Int = 650
    @State private var proteinLeftToday: Int = 35
    @State private var showingImagePicker = false
    @State private var showingTextInput = false
    @State private var selectedImage: UIImage?
    @State private var isAnalyzing = false
    @State private var analysisResult: FoodAnalysisResult?
    @State private var showingAnalysisResult = false
    
    var body: some View {
        NavigationView {
            ZStack {
                // Main TabView with pages
                TabView {
                    // Home View (Progress)
                    HomeView(
                        caloriesSavedThisWeek: caloriesSavedThisWeek,
                        caloriesLeftToday: caloriesLeftToday,
                        proteinLeftToday: proteinLeftToday
                    )
                    .tag(0)
                    
                    // Plan View
                    PlanView()
                    .tag(1)
                }
                .tabViewStyle(PageTabViewStyle(indexDisplayMode: .always))
                .indexViewStyle(PageIndexViewStyle(backgroundDisplayMode: .always))
                
                // Corner buttons that appear on both pages
                VStack {
                    Spacer()
                    
                    HStack {
                        // Camera button - bottom left corner
                        Button(action: {
                            showingImagePicker = true
                        }) {
                            ZStack {
                                Image(systemName: "camera.fill")
                                    .font(.title)
                                    .foregroundColor(.white)
                                    .frame(width: 70, height: 70)
                                    .background(
                                        LinearGradient(
                                            gradient: Gradient(colors: [Color.blue, Color.purple]),
                                            startPoint: .topLeading,
                                            endPoint: .bottomTrailing
                                        )
                                    )
                                    .clipShape(Circle())
                                    .shadow(color: .blue.opacity(0.3), radius: 10, x: 0, y: 5)
                                
                                if isAnalyzing {
                                    ProgressView()
                                        .progressViewStyle(CircularProgressViewStyle(tint: .white))
                                        .scaleEffect(0.8)
                                }
                            }
                        }
                        .disabled(isAnalyzing)
                        
                        Spacer()
                        
                        // Keyboard button - bottom right corner
                        Button(action: {
                            showingTextInput = true
                        }) {
                            Image(systemName: "keyboard.fill")
                                .font(.title)
                                .foregroundColor(.white)
                                .frame(width: 70, height: 70)
                                .background(
                                    LinearGradient(
                                        gradient: Gradient(colors: [Color.green, Color.blue]),
                                        startPoint: .topLeading,
                                        endPoint: .bottomTrailing
                                    )
                                )
                                .clipShape(Circle())
                                .shadow(color: .green.opacity(0.3), radius: 10, x: 0, y: 5)
                        }
                    }
                    .padding(.horizontal, 15)
                    .padding(.bottom, 40)
                }
            }
            .navigationBarHidden(true)
        }
        .sheet(isPresented: $showingImagePicker) {
            ImagePicker(selectedImage: $selectedImage)
        }
        .sheet(isPresented: $showingTextInput) {
            Text("Text Input Coming Soon")
                .font(.title)
                .padding()
        }
        .sheet(isPresented: $showingAnalysisResult) {
            if let result = analysisResult {
                AnalysisResultView(result: result)
            }
        }
        .onChange(of: selectedImage) { _, image in
            if let image = image {
                analyzeFood(image: image)
            }
        }
    }
    
    private func analyzeFood(image: UIImage) {
        isAnalyzing = true
        
        // Convert image to JPEG data
        guard let imageData = image.jpegData(compressionQuality: 0.8) else {
            isAnalyzing = false
            return
        }
        
        // Create multipart form data request
        let url = URL(string: "http://5.161.86.187/api/nutrition/analyze-image")!
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        
        // Add authorization header (you'll need to implement auth)
        // request.setValue("Bearer \(userToken)", forHTTPHeaderField: "Authorization")
        
        // Create multipart form data
        let boundary = UUID().uuidString
        request.setValue("multipart/form-data; boundary=\(boundary)", forHTTPHeaderField: "Content-Type")
        
        var body = Data()
        
        // Add image data
        body.append("--\(boundary)\r\n".data(using: .utf8)!)
        body.append("Content-Disposition: form-data; name=\"image\"; filename=\"food.jpg\"\r\n".data(using: .utf8)!)
        body.append("Content-Type: image/jpeg\r\n\r\n".data(using: .utf8)!)
        body.append(imageData)
        body.append("\r\n--\(boundary)--\r\n".data(using: .utf8)!)
        
        request.httpBody = body
        
        // Make API call
        URLSession.shared.dataTask(with: request) { data, response, error in
            DispatchQueue.main.async {
                isAnalyzing = false
                
                if let error = error {
                    print("API Error: \(error)")
                    return
                }
                
                guard let data = data else { return }
                
                do {
                    if let json = try JSONSerialization.jsonObject(with: data) as? [String: Any],
                       let success = json["success"] as? Bool,
                       success,
                       let analysis = json["analysis"] as? [String: Any],
                       let calories = analysis["calories"] as? Int,
                       let description = analysis["description"] as? String {
                        
                        analysisResult = FoodAnalysisResult(
                            calories: calories,
                            description: description,
                            image: image
                        )
                        showingAnalysisResult = true
                    } else {
                        print("Invalid response format")
                    }
                } catch {
                    print("JSON parsing error: \(error)")
                }
            }
        }.resume()
    }
}

struct FoodAnalysisResult {
    let calories: Int
    let description: String
    let image: UIImage
}

struct ImagePicker: UIViewControllerRepresentable {
    @Binding var selectedImage: UIImage?
    @Environment(\.presentationMode) var presentationMode
    
    func makeUIViewController(context: Context) -> UIImagePickerController {
        let picker = UIImagePickerController()
        picker.delegate = context.coordinator
        picker.sourceType = .camera
        picker.allowsEditing = true
        return picker
    }
    
    func updateUIViewController(_ uiViewController: UIImagePickerController, context: Context) {}
    
    func makeCoordinator() -> Coordinator {
        Coordinator(self)
    }
    
    class Coordinator: NSObject, UIImagePickerControllerDelegate, UINavigationControllerDelegate {
        let parent: ImagePicker
        
        init(_ parent: ImagePicker) {
            self.parent = parent
        }
        
        func imagePickerController(_ picker: UIImagePickerController, didFinishPickingMediaWithInfo info: [UIImagePickerController.InfoKey : Any]) {
            if let image = info[.editedImage] as? UIImage ?? info[.originalImage] as? UIImage {
                parent.selectedImage = image
            }
            parent.presentationMode.wrappedValue.dismiss()
        }
        
        func imagePickerControllerDidCancel(_ picker: UIImagePickerController) {
            parent.presentationMode.wrappedValue.dismiss()
        }
    }
}

struct AnalysisResultView: View {
    let result: FoodAnalysisResult
    @Environment(\.presentationMode) var presentationMode
    
    var body: some View {
        NavigationView {
            VStack(spacing: 20) {
                // Food image
                Image(uiImage: result.image)
                    .resizable()
                    .aspectRatio(contentMode: .fit)
                    .frame(height: 200)
                    .cornerRadius(16)
                    .shadow(radius: 5)
                
                // Calories
                VStack(spacing: 8) {
                    Text("\(result.calories)")
                        .font(.system(size: 48, weight: .thin, design: .default))
                        .foregroundColor(.primary)
                    
                    Text("calories")
                        .font(.headline)
                        .foregroundColor(.secondary)
                }
                
                // Description
                Text(result.description)
                    .font(.body)
                    .foregroundColor(.primary)
                    .multilineTextAlignment(.center)
                    .padding(.horizontal)
                
                Spacer()
                
                // Action buttons
                HStack(spacing: 20) {
                    Button("Add to Log") {
                        // TODO: Add to food log
                        presentationMode.wrappedValue.dismiss()
                    }
                    .font(.headline)
                    .foregroundColor(.white)
                    .frame(maxWidth: .infinity)
                    .frame(height: 50)
                    .background(Color.blue)
                    .cornerRadius(12)
                    
                    Button("Cancel") {
                        presentationMode.wrappedValue.dismiss()
                    }
                    .font(.headline)
                    .foregroundColor(.primary)
                    .frame(maxWidth: .infinity)
                    .frame(height: 50)
                    .background(Color.gray.opacity(0.2))
                    .cornerRadius(12)
                }
                .padding(.horizontal)
                .padding(.bottom, 30)
            }
            .padding()
            .navigationTitle("Food Analysis")
            .navigationBarTitleDisplayMode(.inline)
        }
    }
}

struct HomeView: View {
    let caloriesSavedThisWeek: Int
    let caloriesLeftToday: Int
    let proteinLeftToday: Int
    
    var body: some View {
        // Main content covering the screen
        VStack {
            // Three large numbers, covering more screen space
            VStack(spacing: 70) {
                // Calories saved this week
                VStack(spacing: 4) {
                    Text("\(caloriesSavedThisWeek)")
                        .font(.system(size: 80, weight: .ultraLight, design: .default))
                        .foregroundColor(.primary)
                    
                    Text("calories saved this week")
                        .font(.caption)
                        .foregroundColor(.secondary)
                        .textCase(.lowercase)
                }
                
                // Calories left today
                VStack(spacing: 4) {
                    Text("\(caloriesLeftToday)")
                        .font(.system(size: 80, weight: .ultraLight, design: .default))
                        .foregroundColor(.primary)
                    
                    Text("calories left today")
                        .font(.caption)
                        .foregroundColor(.secondary)
                        .textCase(.lowercase)
                }
                
                // Protein left today
                VStack(spacing: 4) {
                    Text("\(proteinLeftToday)g")
                        .font(.system(size: 80, weight: .ultraLight, design: .default))
                        .foregroundColor(.primary)
                    
                    Text("protein left today")
                        .font(.caption)
                        .foregroundColor(.secondary)
                        .textCase(.lowercase)
                    }
            }
            .multilineTextAlignment(.center)
            .frame(maxWidth: .infinity, maxHeight: .infinity)
            .padding(.top, 40)
            .padding(.bottom, 80)
        }
    }
}

struct PlanView: View {
    var body: some View {
        // Plan content
        ScrollView {
            VStack(spacing: 20) {
                Text("Diet Plan")
                    .font(.system(size: 32, weight: .thin, design: .default))
                    .foregroundColor(.primary)
                    .padding(.top, 60)
                
                // Sample diet plan cards
                VStack(spacing: 16) {
                    DietPlanCard(
                        meal: "Breakfast",
                        calories: 350,
                        protein: 25,
                        description: "Greek yogurt with berries and granola"
                    )
                    
                    DietPlanCard(
                        meal: "Lunch",
                        calories: 450,
                        protein: 35,
                        description: "Grilled chicken salad with quinoa"
                    )
                    
                    DietPlanCard(
                        meal: "Dinner",
                        calories: 500,
                        protein: 40,
                        description: "Salmon with roasted vegetables"
                    )
                    
                    DietPlanCard(
                        meal: "Snack",
                        calories: 150,
                        protein: 10,
                        description: "Apple with almond butter"
                    )
                }
                .padding(.horizontal, 20)
                .padding(.bottom, 80)
            }
        }
    }
}

struct DietPlanCard: View {
    let meal: String
    let calories: Int
    let protein: Int
    let description: String
    
    var body: some View {
        HStack {
            VStack(alignment: .leading, spacing: 8) {
                Text(meal)
                    .font(.headline)
                    .foregroundColor(.primary)
                
                Text(description)
                    .font(.subheadline)
                    .foregroundColor(.secondary)
                    .multilineTextAlignment(.leading)
            }
            
            Spacer()
            
            VStack(alignment: .trailing, spacing: 4) {
                Text("\(calories) cal")
                    .font(.subheadline)
                    .fontWeight(.medium)
                    .foregroundColor(.primary)
                
                Text("\(protein)g protein")
                    .font(.caption)
                    .foregroundColor(.secondary)
            }
        }
        .padding(20)
        .background(Color(.systemBackground))
        .cornerRadius(16)
        .shadow(color: Color.black.opacity(0.05), radius: 8, x: 0, y: 2)
        .overlay(
            RoundedRectangle(cornerRadius: 16)
                .stroke(Color.gray.opacity(0.1), lineWidth: 1)
        )
    }
}

#Preview {
    ContentView()
}
