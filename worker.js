export default {
  async fetch(request, env) {

    if (request.method === "GET") {
      // Devolver el dato que se tenga guardado
      const data = await env.DB.get("arduino_data");
      return new Response(data || "NO_DATA", { status: 200 });
    }

    if (request.method === "POST") {
      const json = await request.text();
      await env.DB.put("arduino_data", json);
      return new Response("OK");
    }

    return new Response("Method not allowed", { status: 405 });
  }
}