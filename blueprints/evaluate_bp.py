"""评价 Blueprint — /api/evaluate, /api/evaluate/*"""
import os, json
from flask import Blueprint, request, jsonify, Response
from evaluator import evaluate_response, kimi_evaluate, kimi_available, dual_evaluate
from services import _safe_str, call_synscale_stream

evaluate_bp = Blueprint("evaluate", __name__)


@evaluate_bp.route("/api/evaluate", methods=["POST"])
def evaluate():
    data = request.get_json()
    question = _safe_str(data.get("question")).strip()
    answer = _safe_str(data.get("answer")).strip()
    if not question or not answer:
        return jsonify({"success": False, "error": "需要 question 和 answer"}), 400
    evaluation = evaluate_response(question, answer)
    if not evaluation:
        return jsonify({"success": False, "error": "评价服务暂不可用"}), 503
    return jsonify({"success": True, "evaluation": evaluation})


@evaluate_bp.route("/api/evaluate/improve", methods=["POST"])
def improve():
    data = request.get_json()
    user_question = _safe_str(data.get("question")).strip()
    agent_answer = _safe_str(data.get("answer")).strip()
    kimi_feedback = _safe_str(data.get("kimi_feedback")).strip()

    if not user_question or not agent_answer:
        return jsonify({"success": False, "error": "需要 question 和 answer"}), 400

    evaluation = evaluate_response(user_question, agent_answer)
    if not evaluation:
        def eg(): yield "data: {\"type\":\"error\",\"message\":\"评价服务暂不可用\"}\n\n"
        return Response(eg(), mimetype="text/event-stream")

    overall = float(evaluation.get("scores", {}).get("overall", 0) or 0)
    if kimi_feedback:
        feedback, force = kimi_feedback, True
    else:
        feedback = f"评分{overall:.1f}/10。请重新回答：{user_question}"
        force = False

    def generate():
        yield f"data: {json.dumps({'type': 'evaluation', 'scores': evaluation.get('scores', {}), 'strengths': evaluation.get('strengths', []), 'weaknesses': evaluation.get('weaknesses', []), 'suggestion': evaluation.get('suggestion', '')}, ensure_ascii=False)}\n\n"
        if force or (evaluation.get("need_improve") and overall < 8.0):
            msgs = [{"role": "user", "content": user_question}, {"role": "assistant", "content": agent_answer}, {"role": "user", "content": feedback}]
            for delta in call_synscale_stream(msgs, tools=None):
                if "error" in delta: break
                c = delta.get("content", "")
                if c:
                    yield f"data: {json.dumps({'type': 'text_improved', 'content': c}, ensure_ascii=False)}\n\n"
        yield "data: {\"type\":\"done\"}\n\n"
    return Response(generate(), mimetype="text/event-stream")


@evaluate_bp.route("/api/evaluate/kimi", methods=["POST"])
def kimi():
    data = request.get_json()
    question = _safe_str(data.get("question")).strip()
    answer = _safe_str(data.get("answer")).strip()
    if not question or not answer:
        return jsonify({"success": False, "error": "需要 question 和 answer"}), 400
    if not kimi_available():
        return jsonify({"success": False, "error": "Kimi API Key 未配置"}), 503
    evaluation = kimi_evaluate(question, answer)
    return jsonify({"success": True, "evaluation": evaluation, "evaluator": "Kimi (Moonshot AI)"})


@evaluate_bp.route("/api/evaluate/dual", methods=["POST"])
def dual():
    data = request.get_json()
    question = _safe_str(data.get("question")).strip()
    answer = _safe_str(data.get("answer")).strip()
    if not question or not answer:
        return jsonify({"success": False, "error": "需要 question 和 answer"}), 400
    result = dual_evaluate(question, answer)
    return jsonify({"success": True, "result": result})
