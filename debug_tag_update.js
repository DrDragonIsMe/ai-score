// 调试标签更新问题的脚本
const axios = require('axios');

// 模拟前端的API调用
async function debugTagUpdate() {
  const headers = {
    'Authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJmcmVzaCI6ZmFsc2UsImlhdCI6MTc1NzEyMjM4MCwianRpIjoiZGU2OTFjYjgtMTVkZS00YTE1LWJmNzEtZjc4MmYwMDIxYThiIiwidHlwZSI6ImFjY2VzcyIsInN1YiI6eyJ1c2VyX2lkIjoiYjliZGEwMzEtZmFiNy00Y2ViLWExZTMtZWZlZDdlNmI3YjE1IiwidGVuYW50X2lkIjoiNGM1ZjIyMzAtZDg5Ny00NDliLWE3OGItZTRkNjNlNDllMjY0Iiwicm9sZSI6ImFkbWluIn0sIm5iZiI6MTc1NzEyMjM4MCwiZXhwIjoxNzU3MjA4NzgwfQ.w_vwfLGVQHL39C6FYK2vgYT9y6umjdgPQobTXMMXHHY',
    'Host': 'default.localhost'
  };

  try {
    console.log('1. 获取知识图谱数据...');
    let response = await axios.get('http://127.0.0.1:5001/api/knowledge-graph?type=ai_assistant_content', { headers });
    let graphs = response.data.data;
    
    if (!graphs || graphs.length === 0) {
      console.log('没有找到AI助理内容，正在创建一个...');
      
      // 获取一个学科ID
      const subjectsResponse = await axios.get('http://127.0.0.1:5001/api/subjects', { headers });
      const subjects = subjectsResponse.data.data;
      if (!subjects || subjects.length === 0) {
        console.error('无法获取学科列表，测试终止');
        return;
      }
      const subjectId = subjects[0].id;

      const createData = {
        subject_id: subjectId,
        name: "AI Assistant Content (Test)",
        description: "Test content created by debug script",
        graph_type: "ai_assistant_content",
        nodes: [{
            id: 'test_node_1',
            name: 'Test Node',
            content: 'Initial content',
            tags: ['initial_tag']
        }],
        edges: []
      };
      
      await axios.post('http://127.0.0.1:5001/api/knowledge-graph', createData, { headers });
      console.log('AI助理内容创建成功');

      // 重新获取
      response = await axios.get('http://127.0.0.1:5001/api/knowledge-graph?type=ai_assistant_content', { headers });
      graphs = response.data.data;
    }
    
    const firstGraph = graphs[0];
    console.log('2. 第一个知识图谱数据:');
    console.log('ID:', firstGraph.id);
    console.log('Name:', firstGraph.name);
    console.log('Tags (记录级别):', firstGraph.tags);
    console.log('Nodes数组:', JSON.stringify(firstGraph.nodes, null, 2));
    
    console.log('\n3. 模拟标签更新...');
    const updateData = {
      tags: ['测试标签1', '测试标签2', '更新后的标签']
    };
    
    const updateResponse = await axios.put(
      `http://127.0.0.1:5001/api/knowledge-graph/nodes/${firstGraph.id}`,
      updateData,
      { headers }
    );
    
    console.log('4. 更新响应:');
    console.log('Success:', updateResponse.data.success);
    console.log('Updated tags:', updateResponse.data.data?.tags);
    console.log('Updated nodes:', JSON.stringify(updateResponse.data.data?.nodes, null, 2));
    
    console.log('\n5. 重新获取数据验证...');
    const verifyResponse = await axios.get(`http://127.0.0.1:5001/api/knowledge-graph/${firstGraph.id}`, { headers });
    const updatedGraph = verifyResponse.data.data;
    
    if (updatedGraph) {
      console.log('验证结果:');
      console.log('Tags (记录级别):', updatedGraph.tags);
      console.log('Nodes数组:', JSON.stringify(updatedGraph.nodes, null, 2));
    }
    
  } catch (error) {
    console.error('调试失败:', error.response?.data || error.message);
  }
}

debugTagUpdate();