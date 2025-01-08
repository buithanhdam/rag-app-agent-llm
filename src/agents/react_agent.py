import json
import logging
from typing import List,Any
from colorama import Fore
from llama_index.core.tools import FunctionTool
from llama_index.core.llms import ChatMessage
from src.agents.llm import BaseLLM
from src.agents.utils import PlanStep, ExecutionPlan, clean_json_response
from src.agents.base import BaseAgent, AgentOptions
logger = logging.getLogger(__name__)


class ReActAgent(BaseAgent):
    """Agent that creates and executes plans using available tools"""
    
    def __init__(self, llm: BaseLLM, options: AgentOptions, tools: List[FunctionTool] = []):
        super().__init__(llm,options)
        self.tools = tools
        self.tools_dict = {tool.metadata.name: tool for tool in tools}
        
    def _create_system_message(self, prompt: str) -> ChatMessage:
        return ChatMessage(role="system", content=prompt)
        
    def _format_tool_signatures(self) -> str:
        """Format all tool signatures into a string format LLM can understand"""
        tool_descriptions = []
        for tool in self.tools:
            metadata = tool.metadata
            parameters = metadata.get_parameters_dict()
            
            tool_descriptions.append(
                f"""
                Function: {metadata.name}
                Description: {metadata.description}
                Parameters: {json.dumps(parameters, indent=2)}
                """
            )
        
        return "\n".join(tool_descriptions)
        
    async def _get_initial_plan(self, task: str) -> ExecutionPlan:
        """Generate initial execution plan for the given task"""
        prompt = f"""
        Create a step-by-step plan to accomplish this task: {task}
        
        Available tools:
        {self._format_tool_signatures()}
        
        Format your response as JSON:
        {{
            "steps": [
                {{
                    "description": "step description",
                    "requires_tool": true/false,
                    "tool_name": "tool_name or null"  // Must match exactly with available tool names
                }},
                ...
            ]
        }}
        Remove the ```json and ```
        """
        
        try:
            response = await self.llm.achat(query=prompt)
            response = clean_json_response(response)
            plan_data = json.loads(response)
            
            plan = ExecutionPlan()
            for step_data in plan_data['steps']:
                # Validate tool name if step requires tool
                if step_data['requires_tool']:
                    tool_name = step_data.get('tool_name')
                    if tool_name not in self.tools_dict:
                        raise ValueError(f"Unknown tool: {tool_name}")
                
                plan.add_step(PlanStep(
                    description=step_data['description'],
                    requires_tool=step_data['requires_tool'],
                    tool_name=step_data.get('tool_name')
                ))
            
            return plan
            
        except Exception as e:
            logger.error(f"Error generating initial plan: {str(e)}")
            raise

    async def _execute_tool(self, step: PlanStep) -> Any:
        """Execute a FunctionTool based on the current step"""
        prompt = f"""
        Generate parameters to call this tool:
        Step: {step.description}
        Tool: {step.tool_name}
        
        Tool specification:
        {json.dumps(self.tools_dict[step.tool_name].metadata.get_parameters_dict(), indent=2)}
        
        Response format:
        {{
            "arguments": {{
                // parameter names and values matching the specification exactly
            }}
        }}
        Remove the ```json and ```
        """
        
        try:
            # Get tool parameters from LLM
            response = await self.llm.achat(query=prompt)
            response = clean_json_response(response)
            params = json.loads(response)
            
            # Get the tool and validate parameters
            tool = self.tools_dict[step.tool_name]
            
            # Execute the tool
            result = await tool.acall(**params['arguments'])
            return result
            
        except Exception as e:
            logger.error(f"Error executing tool {step.tool_name}: {str(e)}")
            raise

    async def run(
        self,
        query: str,
        max_steps: int = 3,
        verbose: bool = False
    ) -> str:
        """Execute the planning and execution process for a given task"""
        
        if verbose:
            print(Fore.BLUE + f"\nGenerating plan for task: {query}")
            
        # Generate initial plan
        plan = await self._get_initial_plan(query)
        
        if verbose:
            print(Fore.GREEN + "\nInitial Plan:")
            for i, step in enumerate(plan.steps):
                print(f"{i+1}. {step.description}")
                if step.requires_tool:
                    print(f"   Using tool: {step.tool_name}")
                
        while not plan.is_complete() and plan.current_step < max_steps:
            current_step = plan.get_current_step()
            
            if verbose:
                print(Fore.YELLOW + f"\nExecuting step {plan.current_step + 1}: {current_step.description}")
                
            try:
                if current_step.requires_tool:
                    result = await self._execute_tool(current_step)
                else:
                    # For non-tool steps, use LLM to execute
                    result = await self.llm.achat(query=current_step.description)
                    
                plan.mark_current_complete(result)
                # Reflect and potentially adjust plan
                # if await self._reflect_and_adjust(plan, result):
                #     if verbose:
                #         print(Fore.MAGENTA + "\nPlan adjusted based on reflection")
                        
            except Exception as e:
                logger.error(f"Error executing step: {str(e)}")
                if verbose:
                    print(Fore.RED + f"\nError in step {plan.current_step + 1}: {str(e)}")
                break
                
        # Generate final summary
        summary_prompt = f"""
        Task completed. Create a summary of what was accomplished:
        Original task: {query}
        Steps completed: {plan.get_progress()}
        Response result: {result}
        """
        
        try:
            summary = await self.llm.achat(query=summary_prompt)
            return summary
            
        except Exception as e:
            logger.error(f"Error generating summary: {str(e)}")
            raise

    async def _reflect_and_adjust(self, plan: ExecutionPlan, last_result: Any) -> bool:
        reflection_prompt = f"""
        Reflect on the current execution state and determine if the plan needs adjustment.
        Only respond with a valid JSON object containing your analysis and decisions.
        
        Current progress: {plan.get_progress()}
        Last result: {last_result}
        Remaining steps: {[step.description for step in plan.steps[plan.current_step + 1:]]}
        
        Available tools: {list(self.tools_dict.keys())}
        
        Respond with a JSON object in this exact format:
        {{
            "decision": "continue",
            "reasoning": "brief explanation",
            "modifications": []
        }}
        
        OR if modifications are needed:
        {{
            "decision": "modify",
            "reasoning": "brief explanation",
            "modifications": [
                {{
                    "type": "add|modify|remove",
                    "step_index": null,
                    "new_description": "step description",
                    "requires_tool": false,
                    "tool_name": null
                }}
            ]
        }}
        Remove the ```json and ```
        """
        
        try:
            response = await self.llm.achat(query=reflection_prompt)
            cleaned_response = clean_json_response(response)
            
            try:
                reflection_data = json.loads(cleaned_response)
            except json.JSONDecodeError as e:
                logger.error(f"JSON parsing error: {str(e)}\nResponse: {cleaned_response}")
                return False
                
            if reflection_data.get("decision") == "continue":
                return False
                
            if reflection_data.get("decision") == "modify":
                modifications = reflection_data.get("modifications", [])
                plan_modified = False
                
                for mod in modifications:
                    try:
                        if mod["type"] == "add":
                            # Validate tool name if step requires tool
                            if mod.get("requires_tool", False):
                                tool_name = mod.get("tool_name")
                                if not tool_name or tool_name not in self.tools_dict:
                                    logger.warning(f"Skipping step with invalid tool: {tool_name}")
                                    continue
                                    
                            new_step = PlanStep(
                                description=mod["new_description"],
                                requires_tool=mod.get("requires_tool", False),
                                tool_name=mod.get("tool_name")
                            )
                            plan.add_step(new_step)
                            plan_modified = True
                            
                        elif mod["type"] == "modify":
                            step_index = mod.get("step_index")
                            if step_index is not None and 0 <= step_index < len(plan.steps):
                                if mod.get("requires_tool", False):
                                    tool_name = mod.get("tool_name")
                                    if not tool_name or tool_name not in self.tools_dict:
                                        logger.warning(f"Skipping modification with invalid tool: {tool_name}")
                                        continue
                                        
                                plan.steps[step_index] = PlanStep(
                                    description=mod["new_description"],
                                    requires_tool=mod.get("requires_tool", False),
                                    tool_name=mod.get("tool_name")
                                )
                                plan_modified = True
                                
                        elif mod["type"] == "remove":
                            step_index = mod.get("step_index")
                            if step_index is not None and 0 <= step_index < len(plan.steps):
                                plan.steps.pop(step_index)
                                plan_modified = True
                                
                    except KeyError as e:
                        logger.error(f"Missing required field in modification: {str(e)}")
                        continue
                        
                return plan_modified
                
        except Exception as e:
            logger.error(f"Error in reflection and adjustment: {str(e)}")
            return False
            
        return False
    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        # Cleanup code if needed
        pass