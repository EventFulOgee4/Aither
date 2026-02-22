from sentence_transformers import SentenceTransformer
EMBEDDER = SentenceTransformer("all-MiniLM-L6-v2")
import numpy as np


class AitherRAG():
    RETRIEVAL_LIMIT = 3

    def __init__(self):
        self.embedder = EMBEDDER
        self.knowledge_base = {
            "cbt": {
                "category": "Cognitive Behavioral Therapy",
                "documents": [
                    "Cognitive restructuring helps identify and challenge negative thought patterns by examining evidence for and against automatic thoughts.",
                    "Behavioral activation encourages engaging in meaningful activities to combat withdrawal and low mood, starting with small achievable goals.",
                    "Thought records track situations, emotions, automatic thoughts, and alternative perspectives to build awareness of thinking patterns.",
                    "Socratic questioning guides the user to examine their beliefs by asking what evidence supports or contradicts their thoughts.",
                    "Cognitive distortions include all-or-nothing thinking, catastrophizing, mind reading, and emotional reasoning which can be identified and reframed."
                ]
            },
            "dbt": {
                "category": "Dialectical Behavior Therapy",
                "documents": [
                    "Distress tolerance skills like TIPP (Temperature, Intense exercise, Paced breathing, Progressive relaxation) help manage acute emotional crises.",
                    "Emotion regulation involves identifying and labeling emotions, understanding their function, and reducing vulnerability to negative emotions.",
                    "Interpersonal effectiveness skills help maintain self-respect and relationships while making requests or saying no using the DEAR MAN technique.",
                    "Radical acceptance means fully accepting reality as it is without judgment, reducing suffering caused by fighting unchangeable circumstances.",
                    "The wise mind concept balances emotional mind and rational mind to make decisions that honor both feelings and logic."
                ]
            },
            "mindfulness": {
                "category": "Mindfulness and Grounding",
                "documents": [
                    "Box breathing involves inhaling for 4 counts, holding for 4 counts, exhaling for 4 counts, and holding for 4 counts to activate the parasympathetic nervous system.",
                    "The 5-4-3-2-1 grounding technique uses the senses: name 5 things you see, 4 you hear, 3 you touch, 2 you smell, and 1 you taste.",
                    "Body scan meditation brings awareness to each part of the body from toes to head, noticing sensations without judgment to release tension.",
                    "Mindful observation involves focusing attention on a single object or sensation for several minutes, gently returning focus when the mind wanders.",
                    "Progressive muscle relaxation systematically tenses and releases muscle groups to reduce physical tension associated with stress and anxiety."
                ]
            },
            "anxiety": {
                "category": "Anxiety Management",
                "documents": [
                    "Exposure therapy gradually confronts feared situations in a controlled way, starting with less anxiety-provoking scenarios and building tolerance.",
                    "Worry time is a scheduled period to process anxious thoughts, training the mind to postpone worry and reduce its intrusion throughout the day.",
                    "Anxiety psychoeducation explains that anxiety is a normal protective response that becomes problematic when activated disproportionately to actual threat.",
                    "Safety behaviors and avoidance maintain anxiety by preventing the person from learning that feared outcomes are unlikely or manageable.",
                    "Challenging catastrophic thinking involves asking what is the worst case, best case, and most likely outcome to gain realistic perspective."
                ]
            },
            "depression": {
                "category": "Depression Support",
                "documents": [
                    "Activity scheduling combats depression by planning pleasurable and mastery activities throughout the week to rebuild engagement and accomplishment.",
                    "Behavioral experiments test negative predictions by trying new behaviors and observing actual outcomes versus expected outcomes.",
                    "Sleep hygiene practices include maintaining consistent sleep and wake times, limiting screen time before bed, and creating a restful environment.",
                    "Social connection even in small doses counteracts isolation, starting with brief low-pressure interactions and gradually increasing social engagement.",
                    "Self-compassion practices involve treating yourself with the same kindness you would offer a friend, recognizing that suffering is part of the human experience."
                ]
            },
            "crisis": {
                "category": "Crisis Resources",
                "documents": [
                    "The 988 Suicide and Crisis Lifeline provides 24/7 free and confidential support by calling or texting 988 in the United States.",
                    "The Crisis Text Line offers free crisis counseling via text by texting HOME to 741741 from anywhere in the United States.",
                    "Safety planning involves identifying warning signs, coping strategies, supportive contacts, and professional resources to use during a crisis.",
                    "Means restriction involves reducing access to lethal means during a crisis, which is one of the most effective suicide prevention strategies.",
                    "A warm handoff to professional care is recommended when someone expresses active suicidal ideation with a plan and access to means."
                ]
            },
            "relationships": {
                "category": "Relationship and Communication",
                "documents": [
                    "Active listening involves fully focusing on the speaker, reflecting back what was heard, and asking clarifying questions without judgment.",
                    "I-statements express feelings and needs without blaming, using the format: I feel [emotion] when [situation] because [reason], and I need [request].",
                    "Boundary setting involves clearly communicating personal limits and consequences while respecting both your own needs and others' autonomy.",
                    "Conflict resolution focuses on understanding both perspectives, identifying shared goals, and finding compromises that address core needs.",
                    "Attachment styles (secure, anxious, avoidant, disorganized) influence relationship patterns and understanding them helps improve relational dynamics."
                ]
            },
            "selfesteem": {
                "category": "Self-Esteem and Identity",
                "documents": [
                    "Core belief work identifies deeply held negative beliefs about the self and systematically gathers evidence to build more balanced self-views.",
                    "Values clarification helps identify what matters most to a person, providing direction and meaning independent of external validation.",
                    "Strengths-based approaches focus on identifying and leveraging personal strengths rather than fixating on weaknesses or deficits.",
                    "Positive data logging involves recording daily evidence that contradicts negative self-beliefs to gradually shift self-perception over time.",
                    "Self-worth is inherent and not contingent on achievement, appearance, or others' approval, which can be reinforced through affirmation practices."
                ]
            }
        }
        self.documents = []
        self.categories = []
        self.embeddings = None
        self.buildIndex()

    def buildIndex(self):
        for key in self.knowledge_base:
            categoryData = self.knowledge_base[key]
            category = categoryData["category"]
            documents = categoryData["documents"]
            for doc in documents:
                self.documents.append(doc)
                self.categories.append(category)
        self.embeddings = self.embedder.encode(self.documents)

    def retrieve(self, query : str, topK : int = RETRIEVAL_LIMIT):
        queryEmbedding = self.embedder.encode([query])
        scores = np.dot(self.embeddings, queryEmbedding.T).flatten()
        topIndices = np.argsort(scores)[::-1][:topK]
        results = []
        for idx in topIndices:
            results.append({
                "document": self.documents[idx],
                "category": self.categories[idx],
                "score": float(scores[idx])
            })
        return results

    def augment(self, query : str, topK : int = RETRIEVAL_LIMIT):
        results = self.retrieve(query, topK)
        context = ""
        for result in results:
            context += result["category"] + ": " + result["document"] + "\n"
        return context
