export async function searchHybrid(query, k = 5) {
  const response = await fetch("http://localhost:8000/search", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ query, k }),
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || "Search request failed");
  }

  return response.json();
}
