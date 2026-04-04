export default async function handler(request, response) {
  const BACKEND_URL = "https://finance-api-docker.onrender.com/";
  
  try {
    const res = await fetch(BACKEND_URL);
    const status = res.status;
    
    return response.status(200).json({
      message: "Render backend pinged successfully",
      status: status,
      timestamp: new Date().toISOString()
    });
  } catch (error) {
    return response.status(500).json({
      message: "Failed to ping Render backend",
      error: error.message
    });
  }
}
