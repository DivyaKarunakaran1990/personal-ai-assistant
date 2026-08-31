import json

from ollama import chat
from sqlalchemy.orm import Session
from models import Memory

from services.memory_service import save_memory, get_memories
from services.document_service import search_documents

from services.shopping_service import (
    add_item,
    get_items,
    remove_item
)

def save_memory_tool(
    db: Session,
    category: str,
    content: str
):
    memory = save_memory(
        db=db,
        category=category,
        content=content
    )

    return {
        "id": memory.id,
        "category": memory.category,
        "content": memory.content
    }


def search_memory_tool(db: Session, query: str):

    memories = get_memories(db)

    query_words = [
        word.lower().strip("?,.!'\"")
        for word in query.split()
        if len(word.strip("?,.!'\"")) > 2
    ]

    matching_memories = []

    for memory in memories:

        content = memory.content.lower()

        score = 0

        for word in query_words:

            # Handle possessives such as "Nilan's"
            clean_word = word.replace("'s", "")

            if clean_word in content:
                score += 1

        if score > 0:

            matching_memories.append(
                {
                    "id": memory.id,
                    "category": memory.category,
                    "content": memory.content,
                    "score": score
                }
            )

    matching_memories.sort(
        key=lambda x: x["score"],
        reverse=True
    )

    return matching_memories[:5]

def add_shopping_item_tool(db: Session, item: str):

    item = item.strip()

    shopping_item = add_item(db, item)

    if shopping_item is None:
        return {
            "success": False,
            "already_exists": True,
            "item": item,
            "message": f"{item} is already on your shopping list."
        }

    return {
        "success": True,
        "already_exists": False,
        "id": shopping_item.id,
        "item": shopping_item.item,
        "message": f"Added {shopping_item.item} to your shopping list."
    }

def get_shopping_list_tool(db: Session):

    items = get_items(db)

    return [
        {
            "id": item.id,
            "item": item.item,
            "completed": item.completed
        }
        for item in items
    ]

def remove_shopping_item_tool(db: Session, item: str):

    shopping_item = remove_item(db, item)

    if not shopping_item:
        return {
            "success": False,
            "message": f"{item} is not on the shopping list."
        }

    return {
        "success": True,
        "message": f"{shopping_item.item} removed from the shopping list."
    }

    if not item:
        return {
            "success": False,
            "message": "Shopping item not found."
        }

    return {
        "success": True,
        "message": f"{item.item} removed from shopping list."
    }

def delete_memory_tool(db: Session, memory_id: int):
    memory = db.query(Memory).filter(Memory.id == memory_id).first()

    if not memory:
        return {
            "success": False,
            "message": "Memory not found"
        }

    db.delete(memory)
    db.commit()

    return {
        "success": True,
        "message": f"Memory {memory_id} deleted"
    }
def ask_ai(message: str, db: Session) -> str:

    message_lower = message.lower()

       # SHOPPING LIST - ADD
    if "shopping list" in message_lower and any(
        word in message_lower
        for word in ["add", "put", "include", "buy"]
    ):
        words = ["add", "put", "include", "buy"]

        item = message_lower

        for word in words:
            item = item.replace(word, "", 1)

        item = item.replace("to my shopping list", "")
        item = item.replace("to the shopping list", "")
        item = item.replace("on my shopping list", "")
        item = item.replace("on the shopping list", "")

        item = item.strip()

        if item:
            result = add_shopping_item_tool(
                db=db,
                item=item
            )

            return f"Added {result['item']} to your shopping list."


    # SHOPPING LIST - REMOVE
    if "shopping list" in message_lower and any(
        word in message_lower
        for word in ["remove", "delete"]
    ):
        words = ["remove", "delete"]

        item = message_lower

        for word in words:
            item = item.replace(word, "", 1)

        item = item.replace("from my shopping list", "")
        item = item.replace("from the shopping list", "")

        item = item.strip()

        if item:
            result = remove_shopping_item_tool(
                db=db,
                item=item
            )

            return result["message"]


    # SHOPPING LIST - SHOW
    if (
        "shopping list" in message_lower
        and not any(
            word in message_lower
            for word in [
                "add",
                "put",
                "include",
                "buy",
                "remove",
                "delete"
            ]
        )
    ):
        shopping_items = get_shopping_list_tool(db)

        if not shopping_items:
            return "Your shopping list is empty."

        return "Your shopping list:\n" + "\n".join(
            f"- {item['item']}"
            for item in shopping_items
        )

    memory_results = search_memory_tool(
        db=db,
        query=message
    )

    print("MEMORY RESULTS:", memory_results)

    if memory_results:

        memory_context = "\n".join(
            f"- {memory['content']}"
            for memory in memory_results
        )

        response = chat(
            model="qwen3:1.7b",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a personal AI assistant. "
                        "Answer the user's question using the stored memory below. "
                        "Do not search documents. "
                        "Do not invent information. "
                        "Give a concise natural answer."
                        f"\n\nSTORED MEMORY:\n{memory_context}"
                    )
                },
                {
                    "role": "user",
                    "content": message
                }
            ]
        )

    return response.message.content

    # If we found relevant stored memories, give them directly to the AI
    # so it doesn't incorrectly search documents instead.
    if memory_results:
        memory_context = "\n".join(
            f"- {memory['content']}"
            for memory in memory_results
        )

        response = chat(
            model="qwen3:1.7b",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a personal AI assistant. "
                        "Answer the user's question using the stored memory below. "
                        "Do not search documents. "
                        "Do not invent information. "
                        "If the memory contains the answer, answer directly and concisely."
                        f"\n\nSTORED MEMORY:\n{memory_context}"
                    )
                },
                {
                    "role": "user",
                    "content": message
                }
            ]
        )

        return response.message.content

        # document_results = search_documents(
        #     db=db,
        #     query=message
        # )

        # print("DOCUMENT RESULTS:", document_results)

        memory_context = ""

        if memory_results:
            memory_context = (
                "\n\nRELEVANT STORED MEMORIES:\n"
                + "\n".join(
                    f"- {memory['content']}"
                    for memory in memory_results
                )
            )

    # document_context = ""

    # if document_results:
    #     document_context = (
    #         "\n\nRELEVANT DOCUMENT INFORMATION:\n"
    #         + "\n".join(
    #             f"- {document['content']}"
    #             for document in document_results
    #         )
    #     )

    tools = [
        {
            "type": "function",
            "function": {
                "name": "search_documents",
                "description": "Search uploaded PDF documents for information relevant to the user's question.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "The information to search for in uploaded documents."
                        }
                    },
                    "required": ["query"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "add_shopping_item",
                "description": "Add an item to the user's shopping list.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "item": {
                            "type": "string",
                            "description": "The item to add."
                        }
                    },
                    "required": ["item"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "get_shopping_list",
                "description": "Get the user's current shopping list.",
                "parameters": {
                    "type": "object",
                    "properties": {}
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "remove_shopping_item",
                "description": "Remove an item from the shopping list by its name.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "item": {
                            "type": "string",
                            "description": "The name of the shopping item to remove."
                        }
                    },
                    "required": ["item"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "delete_memory",
                "description": (
                    "Delete a specific stored memory by its ID. "
                    "Only use this when the user explicitly asks "
                    "to forget or delete information."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "memory_id": {
                            "type": "integer",
                            "description": "The ID of the memory to delete."
                        }
                    },
                    "required": ["memory_id"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "save_memory",
                "description": (
                    "Save important information that the user "
                    "wants the assistant to remember."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "category": {
                            "type": "string",
                            "description": "Memory category."
                        },
                        "content": {
                            "type": "string",
                            "description": "Information to remember."
                        }
                    },
                    "required": ["category", "content"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "search_memory",
                "description": (
                    "Search stored memories to answer questions "
                    "about previously remembered information."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "What information to search for."
                        }
                    },
                    "required": ["query"]
                }
            }
        }
    ]

    messages = [
       {
    "role": "system",
    "content": (
        "You are a personal AI assistant with persistent memory, "
        "shopping list management, and uploaded document search. "

        "IMPORTANT TOOL RULES: "

        "MEMORY: "

        "1. When the user asks you to remember, save, keep, or store "
        "information, use the save_memory tool. "

        "2. When the user asks what you remember or asks about "
        "previously remembered personal information, use search_memory. "

        "3. When the user asks you to forget or delete a memory, "
        "first use search_memory to find the correct memory ID, "
        "then use delete_memory. Never guess an ID. "

        "SHOPPING LIST: "

        "4. When the user asks what is on their shopping list, "
        "use get_shopping_list. "

        "5. When the user asks to add something to the shopping list, "
        "use add_shopping_item. "

        "6. When the user says things such as 'add', 'put', 'include', "
        "'I need', or 'buy' followed by an item and the context is "
        "the shopping list, use add_shopping_item. "

        "7. When the user asks to remove something from the shopping "
        "list, use remove_shopping_item. "

        "8. Never return the shopping list when the user is asking "
        "you to ADD an item. Actually call add_shopping_item. "

        "9. Never return the shopping list when the user is asking "
        "you to REMOVE an item. Actually call remove_shopping_item. "

        "DOCUMENTS: "

        "10. When the user asks about information contained in an "
        "uploaded PDF or document, use search_documents. "

        "11. Questions about rates, bills, invoices, instalments, "
        "amounts, due dates, account balances, or other information "
        "from uploaded documents should use search_documents. "

        "12. When answering from a document, only use information "
        "returned by search_documents. "

        "GENERAL RULES: "

        "13. Never invent, guess, or add information that is not "
        "present in the retrieved tool results. "

        "14. Keep responses concise and natural. "

        "15. After successfully performing an action, tell the user "
        "what you actually did. "

        "16. If an action fails, clearly explain why it failed. "

        "17. Do not claim that something was saved, deleted, added, "
        "or removed unless the corresponding tool returned success. "

        "18. If add_shopping_item reports already_exists=True, "
        "do not say that the item was added. Tell the user that "
        "the item is already on the shopping list."
    )
},
        {
            "role": "user",
            "content": message
        }
    ]

    response = chat(
        model="qwen3:1.7b",
        messages=messages,
        tools=tools
    )

    if not response.message.tool_calls:
        return response.message.content

    for tool_call in response.message.tool_calls:

        tool_name = tool_call.function.name
        arguments = tool_call.function.arguments

        print("TOOL:", tool_name)
        print("ARGUMENTS:", arguments)
        print("DB TYPE:", type(db))

        if tool_name == "search_documents":

            result = search_documents(
                db=db,
                query=arguments["query"]
            )

        elif tool_name == "save_memory":

            result = save_memory_tool(
                db=db,
                category=arguments["category"],
                content=arguments["content"]
            )

        elif tool_name == "search_memory":

            result = search_memory_tool(
                db=db,
                query=arguments["query"]
            )

        elif tool_name == "delete_memory":

            result = delete_memory_tool(
                db=db,
                memory_id=arguments["memory_id"]
            )

        elif tool_name == "add_shopping_item":

            result = add_shopping_item_tool(
                db=db,
                item=arguments["item"]
            )

        elif tool_name == "get_shopping_list":

            result = get_shopping_list_tool(
                db=db
            )

        elif tool_name == "remove_shopping_item":

            result = remove_shopping_item_tool(
                db=db,
                item=arguments["item"]
            )

        else:

            result = {
                "error": "Unknown tool"
            }

        messages.append(response.message)

        messages.append(
            {
                "role": "tool",
                "tool_name": tool_name,
                "content": json.dumps(result)
            }
        )

    final_response = chat(
        model="qwen3:1.7b",
        messages=messages
    )

    return final_response.message.content