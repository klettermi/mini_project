import datetime
import certifi
from pymongo import MongoClient
from flask import Flask, render_template, request, jsonify
app = Flask(__name__)


ca = certifi.where()
url = 'mongodb+srv://sparta:test@cluster0.nzmprle.mongodb.net/?retryWrites=true&w=majority'
client = MongoClient(url, tlsCAFile=ca)

db = client.was


@app.route('/')
def home():
    return render_template('index.html')

#해당 조 주제수집 페이지로 넘어가기
@app.route("/sub_go/<jo_idx>")
def move_sub(jo_idx):
    return render_template('subadd.html')
   
# 해당 조 투표 페이지로 넘어가기
@app.route("/vote_go/<jo_idx>")
def move_vote(jo_idx):
    return render_template('vote.html')

# 최종 주제 페이지로 넘어가기    
@app.route("/result_go/<jo_idx>")
def move_result(jo_idx):
   return render_template('result.html')


    

# 조이름 받기
@app.route("/infoDB", methods=["POST"])
def infoDB_post():
    jo_name = request.form['jo_name_give']
    infoDB_list = list(db.infoDB.find({}, {'_id': False}))
    
    # DB안에 조 이름 있는지 확인 
    for i in infoDB_list:
        if jo_name == i["jo_name"]:
            return jsonify({'msg': '이미 조이름이 있습니다!'})
    
    # 없다면 추가
    count = len(infoDB_list) + 1
    doc = {
        'jo_name': jo_name,
        'jo_idx': count,
        'total_vote':0,
        'sub_active': True,
        'vote_active': False
    }
    db.infoDB.insert_one(doc)
    return jsonify({'msg': '저장완료!'})

#조 이름 검색해서 결과페이지로 넘어가기
@app.route("/findjo", methods=["POST"])
def jo_name_find():
    name_receive = request.form['name_give']
    name_list = list(db.finalDB.find({},{'_id':False}))
    jo_idx=-1
    for i in name_list:
        if name_receive == i["jo_name"]:
            jo_idx = i['jo_idx']
            return jsonify({'result': jo_idx})
    
    if(jo_idx == -1):
        return jsonify({'result': jo_idx})

# 조 정보 주기
@app.route("/infoDB", methods=["GET"])
def jo_info_get():
    infoDB_list = list(db.infoDB.find({}, {'_id': False}))
    return jsonify({'result': infoDB_list})

#주제 목록 주기
@app.route("/subject", methods=["GET"])
def subject2_get():
    all_subject = list(db.voteDB.find({}, {'_id': False}))
    return jsonify({'result': all_subject})

#주제 등록하기
@app.route("/submitsub", methods=["POST"])
def sub_done():
    sub_receive = request.form['sub_give']
    jo_receive = request.form['jo_give']
    a = db.infoDB.find_one({'jo_idx': int(jo_receive)}, {'_id': False})
    name_receive = a['jo_name']
    start_vote = list(db.voteDB.find({'jo_idx': int(jo_receive)}, {'_id': False}))
    leng = len(start_vote)+1
    doc= {
        'jo_name': name_receive,
        'jo_idx': int(jo_receive),
        'subject': sub_receive,
        'sub_idx':leng,
        'vote_cnt':0
    }
    db.voteDB.insert_one(doc)
    return jsonify({'msg': '주제가 등록되었습니다!!'})
#휴지통아이콘 누르면 특정 주제 삭제
@app.route("/delsub", methods=["POST"])
def sub_del():
    sub_receive = request.form['sub_give']
    jo_receive = request.form['jo_give']
    db.voteDB.update_one({'jo_idx': int(jo_receive), 'sub_idx':int(sub_receive)}, {'$set':{'sub_idx': 0}})
    return jsonify({'msg': '선택한 주제가 삭제되었어요!'})

#주제수집 끝내고 투표 시작하기    
@app.route("/startvote", methods=["POST"])
def start_vote():
    idx_receive = request.form['jo_idx']
    db.infoDB.update_one({'jo_idx':int(idx_receive)}, {'$set':{'sub_active':False, 'vote_active':True}})
    return jsonify({'msg': '투표를 시작합니다!!'})

#투표가 발생하면 투표내역 저장
@app.route("/submit", methods=["POST"])
def vote_done():
    vote_receive = request.form['vote_give']
    jo_receive = request.form['jo_give']
    db.voteDB.update_one({'sub_idx': int(vote_receive), 'jo_idx': int(jo_receive)},{'$inc':{'vote_cnt': 1}})
    db.infoDB.update_one({'jo_idx': int(jo_receive)},{'$inc':{'total_vote':1}})
    return jsonify({'msg': '투표가 완료되었습니다!!'})

# 투표 결과로 확정된 주제 finalDB로 POST 
@app.route("/finalDB", methods=["POST"])
def result_post(): 
    jo_receive = request.form['jo_id']
    db.infoDB.update_one({'jo_idx':int(jo_receive)}, {'$set':{'vote_active':False}})
    max_cnt = -1
    all_vote = list(db.voteDB.find({'jo_idx':int(jo_receive)}, {'_id': False}))
    for i in all_vote:
        if(max_cnt < i['vote_cnt']):
            max_cnt = i['vote_cnt']

    for i in all_vote:      
        if (max_cnt == i['vote_cnt']):
            jo_name = i['jo_name']
            jo_idx = i['jo_idx']
            subject = i['subject']
            vote_cnt = i['vote_cnt']
            date = datetime.datetime.now().date()
            dateformat = "%Y-%m-%d"
            t1 = date.strftime(dateformat)
            doc = {'jo_name': jo_name, 'jo_idx': jo_idx, 'subject': subject,
                    'vote_cnt': vote_cnt, 'date': t1}

            db.finalDB.insert_one(doc)
    return jsonify({'msg': '최종 의견이 확정되었습니다!'})

# 확정된 주제들 페이지로 보내기
@app.route("/finalDB", methods=["GET"])
def result_get():
    result_list = list(db.finalDB.find({}, {'_id': False}))
    return jsonify({'result': result_list})

#방명록 등록하기
@app.route("/guestbook", methods=["POST"])
def gb_done():
    jo_receive = request.form['jo_give']
    name_receive = request.form['name_give']
    cmt_receive = request.form['cmt_give']
    doc= {
        'jo_idx': int(jo_receive),
        'guest_name': name_receive,
        'guest_cmt': cmt_receive
    }
    db.guestDB.insert_one(doc)
    return jsonify({'msg': '방명록이 등록되었습니다!!'})

#방명록 주기
@app.route("/guestbook", methods=["GET"])
def gb_get():
    guestbook_list = list(db.guestDB.find({}, {'_id': False}))
    return jsonify({'result': guestbook_list})

if __name__ == '__main__':
    app.run('0.0.0.0', port=5001, debug=True)
