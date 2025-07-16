{
    "experiments": [
        {
            "name": "ladder",
            "game_instances": [
                {
                    "game_id": 0,
                    "graph_id": "53b54b63c64a73h74r83s84c",
                    "m": 10,
                    "n": 10,
                    "named_nodes": [
                        "Bathroom",
                        "Bedroom",
                        "Closet",
                        "Art studio",
                        "Hotel room",
                        "Reception",
                        "Sewing room",
                        "Closet"
                    ],
                    "unnamed_nodes": [
                        "(5, 3)",
                        "(5, 4)",
                        "(6, 3)",
                        "(6, 4)",
                        "(7, 3)",
                        "(7, 4)",
                        "(8, 3)",
                        "(8, 4)"
                    ],
                    "named_edges": [
                        [
                            "Bathroom",
                            "Closet"
                        ],
                        [
                            "Bathroom",
                            "Bedroom"
                        ],
                        [
                            "Bedroom",
                            "Art studio"
                        ],
                        [
                            "Closet",
                            "Hotel room"
                        ],
                        [
                            "Closet",
                            "Art studio"
                        ],
                        [
                            "Art studio",
                            "Reception"
                        ],
                        [
                            "Hotel room",
                            "Sewing room"
                        ],
                        [
                            "Hotel room",
                            "Reception"
                        ],
                        [
                            "Reception",
                            "Closet"
                        ],
                        [
                            "Sewing room",
                            "Closet"
                        ]
                    ],
                    "unnamed_edges": [
                        [
                            "(5, 3)",
                            "(6, 3)"
                        ],
                        [
                            "(5, 3)",
                            "(5, 4)"
                        ],
                        [
                            "(5, 4)",
                            "(6, 4)"
                        ],
                        [
                            "(6, 3)",
                            "(7, 3)"
                        ],
                        [
                            "(6, 3)",
                            "(6, 4)"
                        ],
                        [
                            "(6, 4)",
                            "(7, 4)"
                        ],
                        [
                            "(7, 3)",
                            "(8, 3)"
                        ],
                        [
                            "(7, 3)",
                            "(7, 4)"
                        ],
                        [
                            "(7, 4)",
                            "(8, 4)"
                        ],
                        [
                            "(8, 3)",
                            "(8, 4)"
                        ]
                    ],
                    "node_to_category": {
                        "(5, 3)": "Bathroom",
                        "(5, 4)": "Bedroom",
                        "(6, 3)": "Closet",
                        "(6, 4)": "Art studio",
                        "(7, 3)": "Hotel room",
                        "(7, 4)": "Reception",
                        "(8, 3)": "Sewing room",
                        "(8, 4)": "Closet"
                    },
                    "category_to_node": {
                        "Bathroom": "(5, 3)",
                        "Bedroom": "(5, 4)",
                        "Closet": "(8, 4)",
                        "Art studio": "(6, 4)",
                        "Hotel room": "(7, 3)",
                        "Reception": "(7, 4)",
                        "Sewing room": "(8, 3)"
                    },
                    "node_to_image": {
                        "(5, 3)": "https://www.ling.uni-potsdam.de/clembench/adk/images/ADE/training/home_or_hotel/bathroom/ADE_train_00002866.jpg",
                        "(5, 4)": "https://www.ling.uni-potsdam.de/clembench/adk/images/ADE/training/home_or_hotel/bedroom/ADE_train_00000205.jpg",
                        "(6, 3)": "https://www.ling.uni-potsdam.de/clembench/adk/images/ADE/training/home_or_hotel/closet/ADE_train_00005722.jpg",
                        "(6, 4)": "https://www.ling.uni-potsdam.de/clembench/adk/images/ADE/training/cultural/art_studio/ADE_train_00001751.jpg",
                        "(7, 3)": "https://www.ling.uni-potsdam.de/clembench/adk/images/ADE/training/home_or_hotel/hotel_room/ADE_train_00009615.jpg",
                        "(7, 4)": "https://www.ling.uni-potsdam.de/clembench/adk/images/ADE/training/work_place/reception/ADE_train_00015719.jpg",
                        "(8, 3)": "https://www.ling.uni-potsdam.de/clembench/adk/images/ADE/training/work_place/sewing_room/ADE_train_00016184.jpg",
                        "(8, 4)": "https://www.ling.uni-potsdam.de/clembench/adk/images/ADE/training/home_or_hotel/closet/ADE_train_00005718.jpg"
                    },
                    "category_to_image": {
                        "Bathroom": "https://www.ling.uni-potsdam.de/clembench/adk/images/ADE/training/home_or_hotel/bathroom/ADE_train_00002866.jpg",
                        "Bedroom": "https://www.ling.uni-potsdam.de/clembench/adk/images/ADE/training/home_or_hotel/bedroom/ADE_train_00000205.jpg",
                        "Closet": "https://www.ling.uni-potsdam.de/clembench/adk/images/ADE/training/home_or_hotel/closet/ADE_train_00005718.jpg",
                        "Art studio": "https://www.ling.uni-potsdam.de/clembench/adk/images/ADE/training/cultural/art_studio/ADE_train_00001751.jpg",
                        "Hotel room": "https://www.ling.uni-potsdam.de/clembench/adk/images/ADE/training/home_or_hotel/hotel_room/ADE_train_00009615.jpg",
                        "Reception": "https://www.ling.uni-potsdam.de/clembench/adk/images/ADE/training/work_place/reception/ADE_train_00015719.jpg",
                        "Sewing room": "https://www.ling.uni-potsdam.de/clembench/adk/images/ADE/training/work_place/sewing_room/ADE_train_00016184.jpg"
                    },
                    "start_node": "(7, 4)",
                    "target_node": "(6, 3)",
                    "explorer_prompt": "You are the SEEKER in MapWorld, a network of interconnected rooms.\n\nYour objective is to find and reach the TARGET ROOM.\n\nI have the image of the TARGET ROOM and will describe it to you.\n\nAt each step, you will be shown an image of your current room.\n\nYou may perform only one of the following actions:\n\n1. If the current room exactly matches the TARGET ROOM based on my description, respond strictly with -\nESCAPE\n\n2. If the current room seems similar but you are uncertain, ask me a clarifying question, reply strictly with -\nQUESTION: your question\n\n3. If the current room is definitely not the TARGET ROOM, choose a direction from the available options: $DIRECTIONS$\nreply strictly with -\nMOVE: chosen direction\n\nHere is the description of the TARGET ROOM:\n$INITIAL_DESCRIPTION$\nWhat action do you choose?\n\nYou must follow the above format rules exactly.\nDo not respond in any other format. Do not provide any commentary or clarification.\n\n",
                    "guide_prompt": "You are the GUIDE in MapWorld, a network of interconnected rooms.\n\nYour role is to assist me in reaching the TARGET ROOM.\nYou have access to a single image: the TARGET ROOM.\nI do not know what this room looks like.\nYou do not know the map layout or my current location.\n\nAt each step, you may only respond in one of the following formats:\n\n1. If I ask a question about the TARGET ROOM, reply strictly as:\nANSWER: your answer\n\n2. If I request a description of the TARGET ROOM, reply strictly as:\nDESCRIPTION: your description of the image\n\nDo not respond in any other format. Do not provide any commentary or clarification.\n\nLet’s begin.\n\nPlease describe the TARGET ROOM using:\nDESCRIPTION: your description\n",
                    "explorer_reprompt": "Now you made a move to this room, you can choose one of the following three actions:\n\n1. If the current room exactly matches the TARGET ROOM based on my description, respond strictly with -\nESCAPE\n\n2. If the current room seems similar but you are uncertain, ask me a clarifying question, reply strictly with -\nQUESTION: your question\n\n3. If the current room is definitely not the TARGET ROOM, choose a direction from the available options: $DIRECTIONS$\nreply strictly with -\nMOVE: chosen direction\n\nWhat action do you choose?\n\nYou must follow the above format rules exactly.\nDo not respond in any other format. Do not provide any commentary or clarification.\n\n",
                    "explorer_failed_reprompt": "The move you made is invalid. We remain in the current room. Please carefully review the available directions again.\nYou can now choose one of the following three actions:\n\n1. If the current room exactly matches the TARGET ROOM based on my description, respond strictly with -\nESCAPE\n\n2. If the current room seems similar but you are uncertain, ask me a clarifying question, reply strictly with -\nQUESTION: your question\n\n3. If the current room is definitely not the TARGET ROOM, choose a direction from the available options: $DIRECTIONS$\nreply strictly with -\nMOVE: chosen direction\n\nWhat action do you choose?\n\nYou must follow the above format rules exactly.\nDo not respond in any other format. Do not provide any commentary or clarification.\n\n"
                }
            ]
        }
    ]
}