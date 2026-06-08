from opentelemetry import trace as trace_api
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.resources import Resource
from openinference.instrumentation.google_genai import GoogleGenAIInstrumentor
import phoenix as px

def configure_observability():
    """
    Launches Phoenix, configures OpenTelemetry to send traces to it, 
    and instruments the Google GenAI SDK.
    """
    # 1. Launch the local Phoenix Server (UI) - Disable Jupyter mode and increase timeout
    import os
    os.environ["PHOENIX_ENABLE_PROMETHEUS"] = "false" # Sometimes Prometheus metrics cause slow startup
    os.environ["PHOENIX_PORT"] = "6006"
    os.environ["PHOENIX_HOST"] = "127.0.0.1"
    session = px.launch_app()
    
    # 2. Configure OpenTelemetry to send data to the local Phoenix server
    endpoint = "http://127.0.0.1:6006/v1/traces"
    resource = Resource(attributes={
        "service.name": "nl_to_sql"
    })
    tracer_provider = TracerProvider(resource=resource)
    tracer_provider.add_span_processor(SimpleSpanProcessor(OTLPSpanExporter(endpoint=endpoint)))
    trace_api.set_tracer_provider(tracer_provider)
    
    # 3. Auto-instrument all Google GenAI calls
    GoogleGenAIInstrumentor().instrument()
    
    return session.url
