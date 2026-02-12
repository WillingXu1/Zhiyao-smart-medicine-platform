import { useEffect, useState } from 'react'
import { Table, Input, Button, Space, Tag, Switch, message, Typography } from 'antd'
import { SearchOutlined } from '@ant-design/icons'
import { getUserList, updateUserStatus } from '../../services/api'

const { Title } = Typography

interface User {
  id: number
  username: string
  nickname: string
  phone: string
  status: number
  role: number
  createTime: string
}

const roleMap: Record<number, string> = { 1: '用户', 2: '商家', 3: '管理员', 4: '骑手' }

const UserManage = () => {
  const [loading, setLoading] = useState(false)
  const [users, setUsers] = useState<User[]>([])
  const [total, setTotal] = useState(0)
  const [pageNum, setPageNum] = useState(1)
  const [keyword, setKeyword] = useState('')

  useEffect(() => { fetchUsers() }, [pageNum])

  const fetchUsers = async () => {
    setLoading(true)
    try {
      const res = await getUserList({ pageNum, pageSize: 10, keyword })
      setUsers(res.data?.records || [])
      setTotal(res.data?.total || 0)
    } catch (error) {
      console.error('获取用户列表失败:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleSearch = () => { setPageNum(1); fetchUsers() }

  const handleStatusChange = async (id: number, checked: boolean) => {
    try {
      await updateUserStatus(id, checked ? 1 : 0)
      message.success('状态更新成功')
      fetchUsers()
    } catch (error) {
      console.error('状态更新失败:', error)
    }
  }

  const columns = [
    { title: 'ID', dataIndex: 'id', width: 60 },
    { title: '用户名', dataIndex: 'username', width: 120 },
    { title: '昵称', dataIndex: 'nickname', width: 120 },
    { title: '手机号', dataIndex: 'phone', width: 130 },
    { title: '角色', dataIndex: 'role', width: 100, render: (v: number) => <Tag>{roleMap[v] || '未知'}</Tag> },
    { title: '状态', dataIndex: 'status', width: 100, render: (v: number, record: User) => (
      <Switch checked={v === 1} onChange={(checked) => handleStatusChange(record.id, checked)} checkedChildren="正常" unCheckedChildren="禁用" />
    )},
    { title: '注册时间', dataIndex: 'createTime', width: 180 },
  ]

  return (
    <div>
      <Title level={4}>用户管理</Title>
      <div style={{ marginBottom: 16 }}>
        <Space>
          <Input placeholder="搜索用户名/手机号" value={keyword} onChange={(e) => setKeyword(e.target.value)} onPressEnter={handleSearch} style={{ width: 200 }} />
          <Button icon={<SearchOutlined />} onClick={handleSearch}>搜索</Button>
        </Space>
      </div>
      <Table columns={columns} dataSource={users} rowKey="id" loading={loading}
        pagination={{ current: pageNum, total, pageSize: 10, onChange: setPageNum, showTotal: (t) => `共 ${t} 条` }} />
    </div>
  )
}

export default UserManage
