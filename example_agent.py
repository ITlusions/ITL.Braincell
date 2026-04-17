"""
Example Agent: BrainCell ContextAware Agent

This example demonstrates how to build an agent that uses BrainCell's 
persistent memory via the MCP server to make context-aware decisions.

Usage:
    python example_agent.py
"""

import logging
from typing import Dict, List, Any
from braincell_mcp_client import BrainCellMCPClient
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ContextAwareAgent:
    """
    An example agent that leverages BrainCell's memory for context-aware operations
    """
    
    def __init__(self, braincell_url: str = "http://localhost:9506"):
        """Initialize the agent with BrainCell client"""
        self.client = BrainCellMCPClient(base_url=braincell_url)
        self.context_buffer = []
        logger.info("ContextAwareAgent initialized")
    
    def gather_context(self, task: str) -> Dict[str, Any]:
        """
        Gather relevant context from BrainCell for a task
        
        Args:
            task: Description of the task
        
        Returns:
            Context dictionary with relevant memories
        """
        logger.info(f"Gathering context for task: {task}")
        
        context = {
            "task": task,
            "relevant_decisions": [],
            "relevant_code": [],
            "relevant_architecture": [],
            "similar_past_work": []
        }
        
        # Get relevant context from BrainCell
        try:
            result = self.client.get_relevant_context(task, limit=10)
            
            if result.get('success'):
                data = result.get('data', {})
                context['semantic_results'] = data.get('semantic_results', [])
                context['recent_decisions'] = data.get('recent_decisions', [])
                context['recent_snippets'] = data.get('recent_snippets', [])
                
                logger.info(f"✓ Retrieved {len(context['semantic_results'])} relevant memories")
            else:
                logger.warning(f"Failed to get context: {result.get('error')}")
        
        except Exception as e:
            logger.error(f"Error gathering context: {e}")
        
        return context
    
    def analyze_task(self, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze a task in light of gathered context
        
        Args:
            task: The task description
            context: Context gathered from BrainCell
        
        Returns:
            Analysis results with recommendations
        """
        logger.info("Analyzing task with context")
        
        analysis = {
            "task": task,
            "recommendations": [],
            "warnings": [],
            "related_work": []
        }
        
        # Check if similar work has been done
        similar_work = context.get('semantic_results', [])
        if similar_work:
            analysis['related_work'] = similar_work[:3]
            logger.info(f"Found {len(similar_work)} similar past work items")
        
        # Apply recent decisions to this task
        recent_decisions = context.get('recent_decisions', [])
        if recent_decisions:
            for decision in recent_decisions[:2]:
                analysis['recommendations'].append({
                    "type": "follow_recent_decision",
                    "decision": decision.get('decision'),
                    "rationale": decision.get('rationale')
                })
        
        # Check for relevant code patterns
        recent_snippets = context.get('recent_snippets', [])
        if recent_snippets:
            analysis['recommendations'].append({
                "type": "reuse_code_pattern",
                "snippets": [s.get('title') for s in recent_snippets[:2]]
            })
        
        return analysis
    
    def execute_with_memory(self, task: str) -> Dict[str, Any]:
        """
        Execute a task while leveraging BrainCell's memory
        
        Args:
            task: Task description
        
        Returns:
            Execution result
        """
        logger.info(f"Executing task: {task}")
        
        result = {
            "task": task,
            "status": "planning",
            "steps": [],
            "decision_made": None
        }
        
        # Step 1: Gather context
        logger.info("Step 1: Gathering context")
        context = self.gather_context(task)
        result['steps'].append("context_gathered")
        
        # Step 2: Analyze with context
        logger.info("Step 2: Analyzing task")
        analysis = self.analyze_task(task, context)
        result['steps'].append("analysis_complete")
        result['analysis'] = analysis
        
        # Step 3: Make a decision based on context
        logger.info("Step 3: Making decision")
        decision = self._make_decision(task, analysis)
        result['decision_made'] = decision
        result['steps'].append("decision_made")
        
        # Step 4: Record the decision in BrainCell
        logger.info("Step 4: Recording decision in BrainCell")
        if decision:
            save_result = self.client.save_decision(
                decision=decision['decision'],
                rationale=decision['rationale'],
                impact=decision['impact']
            )
            if save_result.get('success'):
                result['steps'].append("decision_recorded")
                logger.info(f"✓ Decision recorded: {save_result['data']['id']}")
            else:
                result['steps'].append("decision_record_failed")
                logger.warning("Failed to record decision")
        
        result['status'] = "complete"
        return result
    
    def _make_decision(self, task: str, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Make a decision based on task and analysis
        
        Args:
            task: Task description
            analysis: Analysis results
        
        Returns:
            Decision with rationale and impact
        """
        recommendations = analysis.get('recommendations', [])
        related_work = analysis.get('related_work', [])
        
        decision = {
            "decision": f"Execute: {task}",
            "rationale": "",
            "impact": ""
        }
        
        # Build rationale from context
        if related_work:
            decision['rationale'] += f"Based on {len(related_work)} similar past implementations. "
        
        if recommendations:
            decision['rationale'] += f"Applying {len(recommendations)} established patterns. "
        
        decision['rationale'] += "Context retrieved from BrainCell memory system."
        
        decision['impact'] = "Improved consistency with project standards and reduced duplication."
        
        return decision
    
    def save_code_pattern(self, title: str, code: str, language: str, 
                        description: str, tags: List[str]) -> Dict[str, Any]:
        """
        Save a code pattern to BrainCell for future reuse
        
        Args:
            title: Pattern title
            code: Code content
            language: Programming language
            description: Pattern description
            tags: Categorization tags
        
        Returns:
            Save result
        """
        logger.info(f"Saving code pattern: {title}")
        
        result = self.client.save_code_snippet(
            title=title,
            code_content=code,
            language=language,
            description=description,
            tags=tags
        )
        
        if result.get('success'):
            logger.info(f"✓ Pattern saved: {result['data']['id']}")
        else:
            logger.error(f"Failed to save pattern: {result.get('error')}")
        
        return result
    
    def search_knowledge_base(self, query: str) -> Dict[str, Any]:
        """
        Search the knowledge base for relevant information
        
        Args:
            query: Search query
        
        Returns:
            Search results
        """
        logger.info(f"Searching knowledge base: {query}")
        
        result = self.client.search_memory(query, limit=10)
        
        if result.get('success'):
            count = result['data'].get('count', 0)
            logger.info(f"✓ Found {count} relevant items")
        else:
            logger.error(f"Search failed: {result.get('error')}")
        
        return result
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate a report of agent activities"""
        
        report = {
            "agent": "ContextAwareAgent",
            "memory_status": self.client.health_check(),
            "recent_decisions": self.client.get_recent_decisions(limit=5),
            "recent_snippets": self.client.get_recent_snippets(limit=5),
            "memory_summary": {}
        }
        
        # Count items
        try:
            conversations = self.client.list_memories(memory_type="conversations")
            decisions = self.client.list_memories(memory_type="decisions")
            snippets = self.client.list_memories(memory_type="snippets")
            
            report['memory_summary'] = {
                "total_conversations": conversations.get('data', {}).get('count', 0),
                "total_decisions": decisions.get('data', {}).get('count', 0),
                "total_snippets": snippets.get('data', {}).get('count', 0)
            }
        except Exception as e:
            logger.error(f"Failed to get memory summary: {e}")
        
        return report


# ============================================================================
# Example Usage
# ============================================================================

def main():
    """Run example agent scenarios"""
    
    print("\n" + "="*70)
    print("BrainCell ContextAware Agent - Example")
    print("="*70 + "\n")
    
    # Initialize agent
    agent = ContextAwareAgent()
    
    # Example 1: Execute a task with context awareness
    print("📋 Example 1: Execute task with context awareness")
    print("-" * 70)
    
    task = "Design an authentication system for a microservice architecture"
    result = agent.execute_with_memory(task)
    
    print(f"\nTask: {task}")
    print(f"Status: {result['status']}")
    print(f"Steps executed: {' → '.join(result['steps'])}")
    if result.get('decision_made'):
        print(f"Decision: {result['decision_made']['decision']}")
    
    # Example 2: Search knowledge base
    print("\n" + "="*70)
    print("🔍 Example 2: Search knowledge base")
    print("-" * 70)
    
    search_query = "JWT token validation"
    search_results = agent.search_knowledge_base(search_query)
    
    if search_results.get('success') and search_results['data'].get('results'):
        print(f"\nSearch query: {search_query}")
        print(f"Found {search_results['data']['count']} items")
        for item in search_results['data']['results'][:3]:
            print(f"  · {item}")
    
    # Example 3: Save code pattern
    print("\n" + "="*70)
    print("💾 Example 3: Save code pattern")
    print("-" * 70)
    
    jwt_validation_code = '''
def validate_jwt_token(token: str, secret_key: str) -> dict:
    """Validate JWT token and return payload"""
    try:
        import jwt
        payload = jwt.decode(token, secret_key, algorithms=['HS256'])
        return {"valid": True, "payload": payload}
    except jwt.InvalidTokenError as e:
        return {"valid": False, "error": str(e)}
    '''
    
    save_result = agent.save_code_pattern(
        title="JWT Token Validation",
        code=jwt_validation_code,
        language="python",
        description="Validates JWT tokens for API authentication",
        tags=["security", "authentication", "jwt", "pattern"]
    )
    
    print(f"Saved pattern with ID: {save_result['data'].get('id') if save_result.get('success') else 'FAILED'}")
    
    # Example 4: Generate activity report
    print("\n" + "="*70)
    print("📊 Example 4: Agent activity report")
    print("-" * 70)
    
    report = agent.generate_report()
    
    print(f"\nAgent Status: {report['memory_status'].get('status', 'unknown')}")
    
    summary = report.get('memory_summary', {})
    if summary:
        print(f"\nMemory Contents:")
        print(f"  · Conversations: {summary.get('total_conversations', 0)}")
        print(f"  · Decisions: {summary.get('total_decisions', 0)}")
        print(f"  · Code Snippets: {summary.get('total_snippets', 0)}")
    
    print("\n" + "="*70)
    print("✅ Example execution complete!")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
